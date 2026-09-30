# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_bip68_sequence`, one body over either node.

Read from Core's `test/functional/feature_bip68_sequence.py`
(`ab41492c6ba7`, 2026-01-09, the same file at the pinned `v31.1`): the
mempool holds a spend to BIP68's relative lock times, a reorg evicts a
spend whose lock it leaves unmet, a block is not held to them before
the deployment activates, and version 2 transactions are standard.

Core's `run_test` is the body, in its own order, over a pair of nodes
both restarted with Core's own `-testactivationheight=csv@432`
(`Capability.TEST_ACTIVATION_HEIGHT`), and every assertion of Core's
own is kept:

- `test_disable_flag`: a version 2 spend of an unconfirmed coin is
  refused `non-BIP68-final` under a height lock of one block, where the
  disable flag or version 1 lets it in;
- `test_sequence_lock_confirmed_inputs`: random spends of one coin or
  several, each input locked by height, by time or not at all, to just
  within its coin's own age or just past it, are refused exactly when
  one of their locks is not met;
- `test_sequence_lock_unconfirmed_inputs`: a lock other than zero on an
  unconfirmed coin is refused, the same lock on the coin once a block
  holds it is not, and `invalidateblock` (`Capability.INVALIDATE_BLOCK`)
  and a longer fork each return a spend to the mempool, evicting the
  child whose lock that leaves unmet;
- `test_bip68_not_consensus`: before the deployment is active, a block
  carrying a spend the mempool refuses for its lock becomes the tip;
- `activateCSV` and `test_version2_relay`: `getdeploymentinfo` reports
  `csv` active one block before the configured height, and the second
  node, linked to the first (`Capability.CONNECT`), takes a version 2
  spend.

What differs from Core's file:

- the chain Core's framework caches is mined here by `MiniWallet`
  (`mini_wallet.py`), to the same height, so every coinbase of it is the
  wallet's own where Core's wallet owns two runs of them;
- a block Core's node mines from its own mempool is built here
  client-side, carrying the transactions Core's would have taken:
  `MiniWallet.generate`'s own `confirm`, or `build_next_block` where the
  block's time is not the wallet's. So no `prioritisetransaction` keeps
  a spend out of the blocks Core mines past it, and no `setmocktime`
  times them: each carries the time Core's clock gives its node before
  it mines them, and no `Capability.CLOCK` is asked for;
- `build_next_block` and `build_fork` stand in for Core's
  `getblocktemplate` and `create_block`, the fork built where Core takes
  its template, its blocks timed off the wall clock or the median time
  past rather than at Core's own `cur_time`;
- a spend Core's wallet sends to the second node is built by
  `create_self_transfer` and sent over that node's `sendrawtransaction`,
  `MiniWallet` sending only to its own;
- a spend with an input of `MiniWallet`'s beside one paying Core's
  P2WSH `OP_TRUE` output carries each input's own witness, where Core's
  `sign_tx` gives both the wallet's: the refusal it is checked for is
  `non-BIP68-final` either way.

`feature_bip68_sequence_bitcoind_test.py` and
`feature_bip68_sequence_btclib_node_test.py` run the body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import random
import time
from functools import partial
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.amount import sats_from_btc
from btclib.script.script import serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import (
    SEQUENCE_LOCKTIME_DISABLE_FLAG,
    SEQUENCE_LOCKTIME_GRANULARITY,
    SEQUENCE_LOCKTIME_MASK,
    SEQUENCE_LOCKTIME_TYPE_FLAG,
)

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, build_fork, build_next_block
from bitcoin_node_tests.node import connect_nodes, sync_all, wait_until_tips_agree

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.block.block import Block

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.mini_wallet import Utxo
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["mempool_enforces_bip68_before_consensus_does"]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's own `min_activation_height`, which `set_test_params` configures
_CSV_HEIGHT = 432

# what Core's own `set_test_params` starts both nodes with
_ACTIVATION = f"-testactivationheight=csv@{_CSV_HEIGHT}"

# the height of the chain Core's own framework caches
_CHAIN_HEIGHT = 200

# Core's own `NOT_FINAL_ERROR`
_NOT_FINAL = "non-BIP68-final"

# Core's own `RPC_VERIFY_REJECTED`, a refusal by the mempool's own policy
_RPC_VERIFY_REJECTED = -26

# Core's own `SCRIPT_W0_SH_OP_TRUE`: a P2WSH output whose witness script
# is a bare `OP_TRUE`, spent by that script alone
_OP_TRUE = serialize(["OP_TRUE"])
_P2WSH_OP_TRUE = ScriptPubKey.p2wsh(_OP_TRUE, "regtest")

# the nSequence Core's own random spends give an input it leaves unlocked
_NO_LOCK = 0xFFFFFFFE

# Core's own bounds on its random spends: the most outputs a funding
# transaction pays, the spendable coins funded before the spends start,
# how many spends, and the most inputs each spends
_MAX_OUTPUTS = 50
_MIN_UTXOS = 200
_RANDOM_SPENDS = 400
_MAX_INPUTS = 10

# Core's own: the blocks mined past an unconfirmed spend, and the seconds
# its clock moves before each
_BLOCKS_PAST = 10
_BLOCK_INTERVAL = 600

# Core's own 100-block relative lock on the spend no block is held to
_HEIGHT_LOCK = 100


def _hex(tx: Tx) -> str:
    """Return `tx` serialized with its witness, `sendrawtransaction`'s form."""
    return tx.serialize(True, check_validity=False).hex()


def _mempool(node: NodeAdapter) -> set[str]:
    """Return the txids `node`'s own `getrawmempool` answers."""
    return set(node.rpc.call("getrawmempool"))


def _send(node: NodeAdapter, tx: Tx) -> None:
    """Send `tx` over `sendrawtransaction`, which is to take it."""
    assert node.rpc.call("sendrawtransaction", [_hex(tx), 0]) == tx.id.hex()


def _assert_not_final(node: NodeAdapter, tx: Tx) -> None:
    """Check `sendrawtransaction` refuses `tx` for a sequence lock."""
    with pytest.raises(RpcError, match=_NOT_FINAL) as refused:
        node.rpc.call("sendrawtransaction", [_hex(tx), 0])
    assert refused.value.code == _RPC_VERIFY_REJECTED


def _submit(node: NodeAdapter, block: Block) -> object:
    """Return `submitblock`'s own answer for `block`."""
    return node.rpc.call("submitblock", [block.serialize(check_validity=False).hex()])


def _csv_active(node: NodeAdapter) -> bool:
    """Return Core's `softfork_active(node, 'csv')`."""
    return node.rpc.call("getdeploymentinfo")["deployments"]["csv"]["active"] is True


def _median_time_past(node: NodeAdapter, confirmations: int) -> int:
    """Return Core's `get_median_time_past`, `confirmations` below the tip."""
    height = node.rpc.call("getblockcount") - confirmations
    block_hash = node.rpc.call("getblockhash", [height])
    median_time: int = node.rpc.call("getblockheader", [block_hash])["mediantime"]
    return median_time


def _to_op_true(
    wallet: MiniWallet, utxo: Utxo, sequence: int, fee: int, *, version: int = 2
) -> Tx:
    """Return a spend of the wallet's `utxo`, paying `SCRIPT_W0_SH_OP_TRUE`.

    Core's own `CTransaction` over one of its wallet's coins, its output
    the coin less `fee` and signed by `sign_tx`.
    """
    tx = wallet.create_self_transfer(
        utxo_to_spend=utxo, fee=fee, sequence=sequence, version=version
    )
    tx.vout[0] = TxOut(tx.vout[0].value, _P2WSH_OP_TRUE)
    return tx


def _op_true_spend(parent: Tx, sequence: int, fee: int) -> Tx:
    """Return a version 2 spend of `parent`'s `SCRIPT_W0_SH_OP_TRUE` output."""
    tx_in = TxIn(
        OutPoint(parent.id, 0), sequence=sequence, script_witness=Witness([_OP_TRUE])
    )
    tx_out = TxOut(parent.vout[0].value - fee, _P2WSH_OP_TRUE)
    return Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out], check_validity=False)


def _nonzero_locks(
    node: NodeAdapter, orig_tx: Tx, fee: int, *, use_height_lock: bool
) -> Tx:
    """Core's `test_nonzero_locks`: a lock of one on `orig_tx`'s own output.

    Refused while `orig_tx` is in the mempool, taken where it is not.
    """
    sequence = 1 if use_height_lock else 1 | SEQUENCE_LOCKTIME_TYPE_FLAG
    tx = _op_true_spend(orig_tx, sequence, fee)
    if orig_tx.id.hex() in _mempool(node):
        _assert_not_final(node, tx)
    else:
        _send(node, tx)
    return tx


def _disable_flag(
    node: NodeAdapter, wallet: MiniWallet, fee: int, mempool: list[Tx]
) -> None:
    """Core's `test_disable_flag`."""
    parent = wallet.send_self_transfer()
    mempool.append(parent)
    utxo = wallet.get_utxo(txid=parent.id.hex())

    # the disable flag turns off the one-block lock beside it
    sequence = SEQUENCE_LOCKTIME_DISABLE_FLAG | 1
    tx1 = _to_op_true(wallet, utxo, sequence, fee)
    _send(node, tx1)
    mempool.append(tx1)

    # without it, a version 2 spend of the unconfirmed coin is not final
    tx2 = _op_true_spend(tx1, sequence & 0x7FFFFFFF, fee)
    _assert_not_final(node, tx2)

    # version 1 turns the lock off
    tx2.version = 1
    _send(node, tx2)
    mempool.append(tx2)


def _confirmed_inputs(
    nodes: Sequence[NodeAdapter], wallet: MiniWallet, fee: int, mempool: list[Tx]
) -> None:
    """Core's `test_sequence_lock_confirmed_inputs`."""
    node = nodes[0]
    while len(wallet.get_utxos(mark_as_spent=False)) < _MIN_UTXOS:
        num_outputs = random.randint(1, _MAX_OUTPUTS)
        mempool.append(wallet.send_self_transfer_multi(num_outputs=num_outputs))
        wallet.generate(1, confirm=mempool)
        mempool.clear()
        sync_all(nodes)

    tip = node.rpc.call("getblockcount")
    utxos = wallet.get_utxos(mark_as_spent=False)
    for _ in range(_RANDOM_SPENDS):
        num_inputs = random.randint(1, min(_MAX_INPUTS, len(utxos)))
        random.shuffle(utxos)
        should_pass = True
        using_sequence_locks = False
        sequences = []
        for utxo in utxos[:num_inputs]:
            sequence = _NO_LOCK
            if random.randint(0, 1):
                using_sequence_locks = True
                # one in ten is locked to what its coin already meets
                input_will_pass = random.randint(1, 10) == 1
                confirmations = tip - utxo.height + 1 if utxo.confirmed else 0
                sequence = confirmations
                if not input_will_pass:
                    sequence += 1
                    should_pass = False
                # the median time past of the block before the coin's own
                orig_time = _median_time_past(node, confirmations)
                cur_time = _median_time_past(node, 0)
                elapsed = cur_time - orig_time
                can_time_lock = (
                    elapsed >> SEQUENCE_LOCKTIME_GRANULARITY
                ) < SEQUENCE_LOCKTIME_MASK
                if random.randint(0, 1) and can_time_lock:
                    time_delta = sequence << SEQUENCE_LOCKTIME_GRANULARITY
                    if input_will_pass and time_delta > elapsed:
                        sequence = elapsed >> SEQUENCE_LOCKTIME_GRANULARITY
                    elif not input_will_pass and time_delta <= elapsed:
                        sequence = (elapsed >> SEQUENCE_LOCKTIME_GRANULARITY) + 1
                    sequence |= SEQUENCE_LOCKTIME_TYPE_FLAG
            sequences.append(sequence)

        # Core's own overestimate of the size: the unsigned inputs, and room
        # for a signature per input and for the output
        spent = utxos[:num_inputs]
        unsigned = Tx(
            version=2,
            lock_time=0,
            vin=[
                TxIn(utxo.outpoint, sequence=sequence)
                for utxo, sequence in zip(spent, sequences, strict=True)
            ],
            vout=[],
            check_validity=False,
        )
        tx_size = len(unsigned.serialize(False, check_validity=False))
        tx_size += 120 * num_inputs + 50
        # the fee rounded up, as Core's truncated output value rounds it; sent
        # through the wallet, which caches what a spend it takes pays
        send = partial(
            wallet.send_self_transfer_multi,
            utxos_to_spend=spent,
            sequence=sequences,
            fee_per_output=-(-fee * tx_size // 1000),
        )
        if using_sequence_locks and not should_pass:
            with pytest.raises(RpcError, match=_NOT_FINAL) as refused:
                send()
            assert refused.value.code == _RPC_VERIFY_REJECTED
        else:
            mempool.append(send())
            utxos = wallet.get_utxos(mark_as_spent=False)


def _unconfirmed_inputs(
    nodes: Sequence[NodeAdapter], wallet: MiniWallet, fee: int, mempool: list[Tx]
) -> None:
    """Core's `test_sequence_lock_unconfirmed_inputs`."""
    node = nodes[0]
    cur_height = node.rpc.call("getblockcount")

    tx1 = wallet.send_self_transfer()
    mempool.append(tx1)

    # a lock of zero on an unconfirmed coin passes
    tx2 = _to_op_true(wallet, wallet.get_utxo(txid=tx1.id.hex()), 0, fee)
    _send(node, tx2)

    _nonzero_locks(node, tx2, fee, use_height_lock=True)
    _nonzero_locks(node, tx2, fee, use_height_lock=False)

    # blocks past it, carrying what the mempool holds but tx2
    cur_time = int(time.time())
    carried = list(mempool)
    mempool.clear()
    for i in range(_BLOCKS_PAST):
        block = build_next_block(
            node,
            wallet.script_pub_key,
            carried if i == 0 else [],
            time=cur_time + _BLOCK_INTERVAL,
        )
        assert _submit(node, block) is None
        cur_time += _BLOCK_INTERVAL

    assert tx2.id.hex() in _mempool(node)

    _nonzero_locks(node, tx2, fee, use_height_lock=True)
    _nonzero_locks(node, tx2, fee, use_height_lock=False)

    # the fork the reorg below takes, from the tip tx2's block extends,
    # where Core takes its template
    fork = build_fork(node, wallet.script_pub_key, 2)
    block_time = cur_time + _BLOCK_INTERVAL
    block = build_next_block(node, wallet.script_pub_key, [tx2], time=block_time)
    assert _submit(node, block) is None
    sync_all(nodes)
    assert tx2.id.hex() not in _mempool(node)

    # with tx2 confirmed, a time lock on it passes
    tx3 = _nonzero_locks(node, tx2, fee, use_height_lock=False)
    assert tx3.id.hex() in _mempool(node)

    block = build_next_block(node, wallet.script_pub_key, [tx3], time=block_time)
    assert _submit(node, block) is None
    sync_all(nodes)
    assert tx3.id.hex() not in _mempool(node)

    # and a height lock on tx3
    tx4 = _nonzero_locks(node, tx3, fee, use_height_lock=True)
    assert tx4.id.hex() in _mempool(node)

    # a confirmed coin beside an unconfirmed one does not lift the lock
    tx5 = _nonzero_locks(node, tx4, fee, use_height_lock=True)
    assert tx5.id.hex() not in _mempool(node)
    wallet.resync()
    utxo = wallet.get_utxo()
    tx5.vin.append(wallet.create_self_transfer(utxo_to_spend=utxo, sequence=1).vin[0])
    tx5.vout[0] = TxOut(tx5.vout[0].value + utxo.value, _P2WSH_OP_TRUE)
    _assert_not_final(node, tx5)

    # tx3 unconfirmed again: tx4 is no longer final
    node.rpc.call("invalidateblock", [node.rpc.call("getbestblockhash")])
    assert tx4.id.hex() not in _mempool(node)
    assert tx3.id.hex() in _mempool(node)

    # a longer fork leaves tx2 unconfirmed: tx3 is no longer final
    for i, fork_block in enumerate(fork):
        assert _submit(node, fork_block) == (None if i == 1 else "inconclusive")
    pool = _mempool(node)
    assert tx3.id.hex() not in pool
    assert tx2.id.hex() in pool

    # back to where this began, the mempool mined again
    node.rpc.call("invalidateblock", [node.rpc.call("getblockhash", [cur_height + 1])])
    wallet.resync()
    wallet.generate(_BLOCKS_PAST, confirm=[*carried, tx2])


def _not_consensus(node: NodeAdapter, wallet: MiniWallet, fee: int) -> None:
    """Core's `test_bip68_not_consensus`."""
    assert not _csv_active(node)

    tx1 = wallet.send_self_transfer()
    tx2 = _to_op_true(wallet, wallet.get_utxo(txid=tx1.id.hex()), 0, fee, version=1)
    _send(node, tx2)

    # the mempool refuses a spend of tx2 locked for a hundred blocks
    tx3 = _op_true_spend(tx2, _HEIGHT_LOCK, fee)
    _assert_not_final(node, tx3)

    # a block carrying it becomes the tip
    block = build_next_block(node, wallet.script_pub_key, [tx1, tx2, tx3])
    assert _submit(node, block) is None
    assert node.rpc.call("getbestblockhash") == block.header.hash.hex()


def _activate_csv(nodes: Sequence[NodeAdapter], wallet: MiniWallet) -> None:
    """Core's `activateCSV`: active one block before the configured height."""
    node = nodes[0]
    wallet.resync()
    height = node.rpc.call("getblockcount")
    assert _CSV_HEIGHT - height > 2
    wallet.generate(_CSV_HEIGHT - height - 2)
    assert not _csv_active(node)
    wallet.generate(1)
    assert _csv_active(node)
    wait_until_tips_agree(nodes)


def mempool_enforces_bip68_before_consensus_does(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    nodes = cluster(2)
    node0, node1 = nodes
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.TEST_ACTIVATION_HEIGHT, node0.capabilities, skip_counts)
    require(Capability.INVALIDATE_BLOCK, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    for node in nodes:
        node.restart([_ACTIVATION])
    connect_nodes(node1, node0)
    wallet = MiniWallet(node0)
    wallet.generate(_CHAIN_HEIGHT)
    sync_all(nodes)

    fee = sats_from_btc(node0.rpc.call("getnetworkinfo")["relayfee"])

    # what the next block Core's node mines carries, in the order the first
    # node took each
    mempool: list[Tx] = []
    _disable_flag(node0, wallet, fee, mempool)
    _confirmed_inputs(nodes, wallet, fee, mempool)
    _unconfirmed_inputs(nodes, wallet, fee, mempool)
    _not_consensus(node0, wallet, fee)
    _activate_csv(nodes, wallet)

    # version 2 is standard on the second node
    tx = wallet.create_self_transfer(version=2)
    _send(node1, tx)
