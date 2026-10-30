# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_reorg`, as bodies over each node.

Read from Core's `test/functional/mempool_reorg.py` (`fa3aeb51cfb1`,
2026-10-26): spends of coinbases, direct and
indirect, and a spend time-locked past the tip's median time past, go in
and out of the mempool as a reorg makes each immature, non-final or
unconfirmed again; and a transaction a reorg returns from a disconnected
block is served to a peer asking for it before the node has announced
it, where one no block has held is not.

Core's `test_reorg` is the coinbase body and its `test_reorg_relay` the
relay body, each over a fresh node, and every assertion of Core's own is
kept. Each reorg is the node taking a longer fork submitted to it, Core's
`trigger_reorg`. The coinbase body asks for `Capability.MINE` and
`Capability.INVALIDATE_BLOCK`; the relay body for `Capability.MINE` and
`Capability.CLOCK`.

What differs from Core's file:

- the chain Core's framework caches is mined here by `MiniWallet`
  (`mini_wallet.py`), to the same height, so the coinbases Core spends
  and the block it invalidates sit at Core's own heights; the relay body
  mines its own coins first, Core's running on the chain `test_reorg`
  left;
- a block Core's node mines from its own mempool is built here
  client-side, carrying the transactions Core's would have taken:
  `MiniWallet.generate`'s own `confirm`, or `build_next_block` where the
  block's time is not the wallet's, or where a reorg leaves the block
  out, which the wallet would keep as its tip. The run of blocks that
  moves the median time past beyond the time lock carries times one
  second apart from that lock on, the time Core's `setmocktime` gives
  its node before it mines them; the coinbase body sets no clock, its
  blocks carrying their own times;
- `build_fork` stands in for Core's `create_empty_fork`
  (`blocktools.py`), its blocks timed off the wall clock rather than one
  second apart from the tip's own time;
- Core's `P2PTxInvStore` answers every `inv` with a `getdata` from its
  framework's network thread and counts the transactions announced;
  `_sync` here does both while it waits for a ping's own `pong`, and
  runs before each of Core's reads of what the peer received.

Each `mempool_reorg_<node>_test.py` module beside this one runs each
body, `tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
import time
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError, magic_from_chain
from btclib.p2p import GetData, Inv, Inventory, InventoryType, Ping, Pong, TxPayload
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, build_fork, build_next_block
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.block.block import Block
    from btclib.tx import Tx

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "disconnected_transactions_are_available_for_relay",
    "reorgs_evict_immature_and_non_final_spends",
]

type _Cluster = Callable[[int], Sequence[NodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# the height of the chain Core's own framework caches
_CHAIN_HEIGHT = 200

# Core's own: the block holding the first coinbase `test_reorg` spends
_FIRST_BLOCK = 76

# Core's own `FORK_LENGTH`: the fork outweighs the chain the node takes
# meanwhile, one block shorter
_FORK_LENGTH = 20

# Core's own length of the fork the relay body reorgs to, longer than the
# one block it leaves out
_RELAY_FORK_LENGTH = 3

# Core's own: how far past the clock the time-locked spend is locked
_TIMELOCK = 300

# Core's own: the descendants chained off `spend_2_1`
_DESCENDANTS = 10

# the coins the relay body spends: tx_disconnected, tx_before_reorg and
# tx_after_reorg, each a matured coinbase of its own
_RELAY_SPENDS = 3

# Core's own advance of the node's clock, after which it announces what its
# mempool holds
_ANNOUNCE_ADVANCE = 300

# Core's own `RPC_VERIFY_REJECTED`, a refusal by the mempool's own policy
_RPC_VERIFY_REJECTED = -26

# `Peer`'s own default wait, for a read that bypasses `wait_for`
_RECEIVE_TIMEOUT = 30.0


def _hex(tx: Tx) -> str:
    """Return `tx` serialized with its witness, `sendrawtransaction`'s form."""
    return tx.serialize(True, check_validity=False).hex()


def _mempool(node: NodeAdapter) -> set[str]:
    """Return the txids `node`'s own `getrawmempool` answers."""
    return set(node.rpc.call("getrawmempool"))


def _submit(node: NodeAdapter, block: Block) -> None:
    """Submit `block` to `node`, which is to take it as its new tip."""
    answer = node.rpc.call("submitblock", [block.serialize(check_validity=False).hex()])
    assert answer is None


def _trigger_reorg(node: NodeAdapter, fork: Sequence[Block]) -> None:
    """Core's own `trigger_reorg`: `fork` submitted, its last block the tip."""
    for block in fork:
        node.rpc.call("submitblock", [block.serialize(check_validity=False).hex()])
    assert node.rpc.call("getbestblockhash") == fork[-1].header.hash.hex()


def _tip_time(node: NodeAdapter) -> int:
    """Return the time `node`'s own tip carries, Core's `getblock` read."""
    block_time = node.rpc.call("getblock", [node.rpc.call("getbestblockhash")])["time"]
    assert isinstance(block_time, int)
    return block_time


def reorgs_evict_immature_and_non_final_spends(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_reorg`, in its own order.

    :param cluster: a node's own cluster fixture.
    :param skip_counts: the session's own tally.
    """
    (node0,) = cluster(1)
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.INVALIDATE_BLOCK, node0.capabilities, skip_counts)
    wallet = MiniWallet(node0)
    wallet.generate(_CHAIN_HEIGHT)
    now = int(time.time())

    assert node0.rpc.call("getblockcount") == _CHAIN_HEIGHT

    # three coinbase spends a reorg makes immature: spend_1 directly;
    # spend_2 in the chain and its child spend_2_1 in the mempool; spend_3
    # and its child spend_3_1 both in the chain
    hashes = [node0.rpc.call("getblockhash", [_FIRST_BLOCK + i]) for i in range(4)]
    coinbase_txids = [node0.rpc.call("getblock", [h])["tx"][0] for h in hashes]
    utxo_1 = wallet.get_utxo(txid=coinbase_txids[1])
    utxo_2 = wallet.get_utxo(txid=coinbase_txids[2])
    utxo_3 = wallet.get_utxo(txid=coinbase_txids[3])
    spend_1 = wallet.create_self_transfer(utxo_to_spend=utxo_1)
    spend_2 = wallet.create_self_transfer(utxo_to_spend=utxo_2)
    spend_3 = wallet.create_self_transfer(utxo_to_spend=utxo_3)

    # a fourth, time-locked to Core's own margin past the clock
    future = now + _TIMELOCK
    utxo = wallet.get_utxo(txid=coinbase_txids[0])
    timelock_tx = wallet.create_self_transfer(utxo_to_spend=utxo, locktime=future)

    with pytest.raises(RpcError, match="non-final") as refused:
        node0.rpc.call("sendrawtransaction", [_hex(timelock_tx)])
    assert refused.value.code == _RPC_VERIFY_REJECTED

    node0.rpc.call("sendrawtransaction", [_hex(spend_2)])
    node0.rpc.call("sendrawtransaction", [_hex(spend_3)])
    wallet.generate(1, confirm=[spend_2, spend_3])
    with pytest.raises(RpcError, match="non-final") as refused:
        node0.rpc.call("sendrawtransaction", [_hex(timelock_tx)])
    assert refused.value.code == _RPC_VERIFY_REJECTED

    spend_2_1 = wallet.create_self_transfer(
        utxo_to_spend=wallet.new_utxos(spend_2)[0], version=1
    )
    spend_3_1 = wallet.create_self_transfer(utxo_to_spend=wallet.new_utxos(spend_3)[0])
    node0.rpc.call("sendrawtransaction", [_hex(spend_3_1)])

    fork = build_fork(node0, wallet.script_pub_key, _FORK_LENGTH)

    # one block fewer than the fork, from the lock's own time on: the
    # median time past moves past the lock, and spend_3_1 is confirmed
    for i in range(_FORK_LENGTH - 1):
        carried = [spend_3_1] if i == 0 else []
        _submit(
            node0,
            build_next_block(node0, wallet.script_pub_key, carried, time=future + i),
        )
    block_time = _tip_time(node0)
    assert block_time >= now + _TIMELOCK

    # the time-locked spend is final now
    timelock_tx_id = node0.rpc.call("sendrawtransaction", [_hex(timelock_tx)])
    spend_1_id = node0.rpc.call("sendrawtransaction", [_hex(spend_1)])
    spend_2_1_id = node0.rpc.call("sendrawtransaction", [_hex(spend_2_1)])
    assert _mempool(node0) == {spend_1_id, spend_2_1_id, timelock_tx_id}

    _trigger_reorg(node0, fork)

    # back in time: the lock is not final any more, and spend_3_1 is
    # unconfirmed again
    assert _tip_time(node0) < block_time
    assert _mempool(node0) == {spend_1_id, spend_2_1_id, spend_3_1.id.hex()}

    spend_2_id = spend_2.id.hex()
    while spend_2_id not in _mempool(node0):
        node0.rpc.call("invalidateblock", [node0.rpc.call("getbestblockhash")])
    assert spend_2_id in _mempool(node0)
    assert spend_2_1_id in _mempool(node0)

    parent_utxo = wallet.new_utxos(spend_2_1)[0]
    for _ in range(_DESCENDANTS):
        tx = wallet.create_self_transfer(utxo_to_spend=parent_utxo, version=1)
        node0.rpc.call("sendrawtransaction", [_hex(tx)])
        parent_utxo = wallet.new_utxos(tx)[0]

    # back far enough that every coinbase spend above is immature again
    invalid = node0.rpc.call("getblockhash", [_FIRST_BLOCK + COINBASE_MATURITY])
    node0.rpc.call("invalidateblock", [invalid])
    assert _mempool(node0) == set()


def _sync(peer: Peer, invs: set[bytes]) -> None:
    """Round-trip two `ping`s, answering and recording each `inv` meanwhile.

    `Peer.sync_with_ping`'s own barrier, and Core's `P2PTxInvStore` over
    it: an `inv` is answered with a `getdata` for every entry of a
    defined type, `P2PInterface.on_inv`'s own, and the hash of every
    `MSG_TX` or `MSG_WTX` entry joins `invs`, `tx_invs_received`'s own
    keys. Every message read on the way is `Peer.last_message`'s.

    :raises TimeoutError: the second `pong` did not arrive in time.
    """
    nonce = secrets.randbelow(2**64 - 1) + 1
    peer.send(Ping(0))
    peer.send(Ping(nonce))
    deadline = time.monotonic() + scaled(_RECEIVE_TIMEOUT)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            err_msg = "never saw the pong within the wait"
            raise TimeoutError(err_msg)
        message = peer.receive(timeout=remaining)
        if message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            wanted = [
                item for item in items if item.type_code != InventoryType.UNDEFINED
            ]
            if wanted:
                peer.send(GetData(wanted))
            tx_types = {InventoryType.MSG_TX, InventoryType.MSG_WTX}
            invs.update(item.hash for item in items if item.type_code in tx_types)
        elif message.command == "pong" and Pong.parse(message.payload).nonce == nonce:
            return


def _received_tx(peer: Peer) -> Tx:
    """Return the transaction of the last `tx` message `peer` received."""
    return TxPayload.parse(peer.last_message["tx"].payload, check_validity=False).tx


def disconnected_transactions_are_available_for_relay(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_reorg_relay`, in its own order.

    :param cluster: a node's own cluster fixture.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    wallet = MiniWallet(node)

    node.set_mock_time(int(time.time()))
    wallet.generate(COINBASE_MATURITY + _RELAY_SPENDS)

    # a longer chain, in which tx_disconnected is not confirmed
    fork = build_fork(node, wallet.script_pub_key, _RELAY_FORK_LENGTH)
    invs: set[bytes] = set()
    with Peer(node.p2p_address, _MAGIC) as peer1:
        peer1.handshake()
        _sync(peer1, invs)

        # confirmed in a block the fork leaves out
        tx_disconnected = wallet.create_self_transfer()
        node.rpc.call("sendrawtransaction", [_hex(tx_disconnected)])
        block = build_next_block(node, wallet.script_pub_key, [tx_disconnected])
        _submit(node, block)

        tx_before_reorg = wallet.create_self_transfer()
        node.rpc.call("sendrawtransaction", [_hex(tx_before_reorg)])
        tx_child = wallet.create_self_transfer(
            utxo_to_spend=wallet.new_utxos(tx_disconnected)[0]
        )
        node.rpc.call("sendrawtransaction", [_hex(tx_child)])
        entry = node.rpc.call("getmempoolentry", [tx_child.id.hex()])
        assert entry["ancestorcount"] == 1
        _sync(peer1, invs)
        assert len(invs) == 0

        _trigger_reorg(node, fork)

        # the child now has an ancestor from the disconnected block
        entry = node.rpc.call("getmempoolentry", [tx_child.id.hex()])
        assert entry["ancestorcount"] == 2
        entry = node.rpc.call("getmempoolentry", [tx_before_reorg.id.hex()])
        assert entry["ancestorcount"] == 1

        # no clock has moved to announce any of them, and the two no block
        # has held are too recent to be served
        _sync(peer1, invs)
        assert len(invs) == 0
        too_recent = [
            Inventory(InventoryType.MSG_WTX, tx.hash)
            for tx in (tx_before_reorg, tx_child)
        ]
        peer1.send(GetData(too_recent))
        _sync(peer1, invs)
        for _ in too_recent:
            _sync(peer1, invs)
        assert "tx" not in peer1.last_message
        assert "notfound" in peer1.last_message

        # never announced, and in the mempool later than those two, but
        # served: it came back from a disconnected block
        peer1.send(GetData([Inventory(InventoryType.MSG_WTX, tx_disconnected.hash)]))
        _sync(peer1, invs)
        assert len(invs) == 0
        assert _received_tx(peer1).hash == tx_disconnected.hash

        node.set_mock_time(int(time.time()) + _ANNOUNCE_ADVANCE)
        _sync(peer1, invs)
        assert len(invs) == 3
        for _ in range(3):
            _sync(peer1, invs)
        last_tx_received = peer1.last_message["tx"]

        tx_after_reorg = wallet.create_self_transfer()
        node.rpc.call("sendrawtransaction", [_hex(tx_after_reorg)])
        assert tx_after_reorg.id.hex() in _mempool(node)
        peer1.send(GetData([Inventory(InventoryType.MSG_WTX, tx_after_reorg.hash)]))
        _sync(peer1, invs)
        assert peer1.last_message["tx"] == last_tx_received
