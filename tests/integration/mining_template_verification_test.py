# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mining_template_verification`, one body over either node.

Read from Core's `test/functional/mining_template_verification.py`
(`6eca11175be6`, 2026-07-16): the node checks a block handed to
`getblocktemplate` in BIP23's `proposal` mode
(`Capability.BLOCK_PROPOSAL`) without storing it or asking for its
proof-of-work, answering `null` for a valid one and the reason it
refuses an invalid one, and `submitblock` refuses each invalid one after
it. Every assertion Core's file makes is kept, in its order, each reason
copied from it.

`MiniWallet` (`Capability.MINE`) mines the block Core's framework mines
before the first proposal, and builds the transaction the later
proposals carry. It needs a mature coin, so it first mines
`COINBASE_MATURITY` blocks, where Core's own node starts on a chain its
framework already mined.

The blocks under test are built here with btclib, the way Core's
`create_block` and `add_witness_commitment` (`blocktools.py`) build
them: header version `4`, regtest's own bits, and a coinbase of
`create_coinbase`'s own shape, its lock time one below its height and
its input's sequence `MAX_SEQUENCE_NONFINAL`, so that the lock time
Core's non-final case sets is enforced. btclib's `build_coinbase` sets
the final sequence instead. Each of Core's tamperings is made to a copy
of that block. Core's `uint256` fields are integers, and btclib keeps
each hash in display order, so an increment is on that integer.

Where Core waits for height `2` after submitting its block, a height its
framework's chain is already past, this waits for the height of the
block it submitted. Core times the blocks on top of that one a second
past `block_1`'s median time. `MiniWallet` times each block it mines by
the wall clock, at least a second past the one before, so on this chain
`block_2`'s own median time can reach that second, which a block on top
of `block_2` has to exceed: those blocks are timed a second past
`block_2`'s median time instead.

Core checks proposals from several threads over `bitcoin-cli`, a program
this repository does not run; here each thread holds an RPC client of
its own (`NodeAdapter.rpc`), concurrency being the subject.

`mining_template_verification_bitcoind_test.py` and
`mining_template_verification_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.block.block import (
    Block,
    bip34_commitment,
    merkle_root_and_mutated_from_transactions,
    witness_commitment_output,
)
from btclib.block.block_header import BlockHeader
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS, subsidy
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["a_proposed_block_is_checked_and_not_stored"]

# Core's own `NORMAL_GBT_REQUEST_PARAMS` (`blocktools.py`)
_NORMAL_GBT_REQUEST_PARAMS = {"rules": ["segwit"]}

# Core's own `VERSIONBITS_LAST_OLD_BLOCK_VERSION`, `create_block`'s default
_VERSION = 4

# Core's own `MAX_SEQUENCE_NONFINAL` (`messages.py`), `create_coinbase`'s
_MAX_SEQUENCE_NONFINAL = 0xFFFFFFFE

# `CScript([OP_TRUE])`, the output `create_coinbase` pays by default
_OP_TRUE = b"\x51"

# Core's own "impossible in the real world" bits
_EXTREMELY_HIGH_BITS = 469762303

# Core's own over-spent value: 100 BTC, where the coin spent holds 50
_OVERSPENT_VALUE = 10_000_000_000

# Core's own thread count, and the checks each thread makes
_THREADS = 6
_CHECKS_PER_THREAD = 50

# `src/rpc/protocol.h`'s own `RPC_DESERIALIZATION_ERROR`
_DESERIALIZATION_ERROR = -22

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval


def _plus(value: bytes, increment: int) -> bytes:
    """Return a display-order hash, as Core's `uint256`, plus `increment`."""
    return (int.from_bytes(value, "big") + increment).to_bytes(32, "big")


def _uint256(value: int) -> bytes:
    """Return Core's `uint256` integer `value` as a display-order hash."""
    return value.to_bytes(32, "big")


def _create_coinbase(height: int) -> Tx:
    """Core's `create_coinbase`: `height` committed, paying `OP_TRUE`."""
    return Tx(
        version=2,
        lock_time=height - 1,
        vin=[
            TxIn(
                OutPoint(),
                bip34_commitment(height),
                _MAX_SEQUENCE_NONFINAL,
                check_validity=False,
            )
        ],
        vout=[TxOut(subsidy(height, _HALVING_INTERVAL), _OP_TRUE)],
        check_validity=False,
    )


def _calc_merkle_root(block: Block) -> bytes:
    """Core's `calc_merkle_root`, over the block's own transactions."""
    return merkle_root_and_mutated_from_transactions(block.transactions)[0]


def _create_block(
    hashprev: bytes, height: int, ntime: int, txlist: Sequence[Tx] = ()
) -> Block:
    """Core's `create_block`: unsolved, over a fresh coinbase and `txlist`."""
    header = BlockHeader(
        version=_VERSION,
        previous_block_hash=hashprev,
        time=datetime.fromtimestamp(ntime, UTC),
        bits=REGTEST_POW_LIMIT_BITS,
        check_validity=False,
    )
    block = Block(header, [_create_coinbase(height), *txlist], check_validity=False)
    header.merkle_root = _calc_merkle_root(block)
    return block


def _add_witness_commitment(block: Block) -> None:
    """Core's `add_witness_commitment`, with its own all-zero nonce."""
    nonce = b"\x00" * 32
    commitment = witness_commitment_output(block.transactions, nonce)
    coinbase = block.transactions[0]
    coinbase.vin[0].script_witness = Witness([nonce], check_validity=False)
    coinbase.vout.append(commitment)
    block.header.merkle_root = _calc_merkle_root(block)


def _hash_int(block: Block) -> int:
    """Core's `hash_int`: the header's own hash, as an integer."""
    return int.from_bytes(block.header.hash, "big")


def _solve(block: Block) -> None:
    """Core's `CBlock.solve`: the nonce raised until the hash meets the bits.

    Not `btclib.block.mining.mine`, which validates the header it copies
    and so refuses the time Core's `time-too-old` case submits.
    """
    target = int.from_bytes(block.header.target, "big")
    while _hash_int(block) > target:
        block.header.nonce += 1


def _hex(block: Block) -> str:
    """Return the block's own serialization, witnesses included, in hex."""
    return block.serialize(check_validity=False).hex()


def _proposal(data: str) -> dict[str, object]:
    """Return the `template_request` Core's file proposes `data` in."""
    return {"data": data, "mode": "proposal", **_NORMAL_GBT_REQUEST_PARAMS}


def _assert_template(
    rpc: BitcoinCoreRpcClient,
    block: Block,
    expect: str | None,
    *,
    rehash: bool = True,
    submit: bool = True,
    solve: bool = True,
    expect_submit: str | None = None,
) -> None:
    """Core's own `assert_template`, over one RPC client.

    :param expect: the proposal's own answer, `None` for a valid block.
    :param rehash: recompute the merkle root first.
    :param submit: where `expect` is not `None`, also submit the block.
    :param solve: solve the block before submitting it.
    :param expect_submit: `submitblock`'s own answer, where it is not
        `expect`.
    """
    if rehash:
        block.header.merkle_root = _calc_merkle_root(block)
    answer = rpc.call("getblocktemplate", {"template_request": _proposal(_hex(block))})
    assert answer == expect
    # only an invalid block is submitted
    if submit and expect is not None:
        if expect_submit is None:
            expect_submit = expect
        if solve:
            _solve(block)
        assert rpc.call("submitblock", [_hex(block)]) == expect_submit


def _decode_failed(node: NodeAdapter, data: str) -> None:
    """Assert the proposal of `data` is refused as a block that does not decode.

    Of the node's own message alone: `RpcError`'s text opens with the
    method and the endpoint (`bitcoin_core_rpc`'s own `_result`).
    """
    client = node.rpc
    with pytest.raises(RpcError) as excinfo:
        client.call("getblocktemplate", {"template_request": _proposal(data)})
    assert excinfo.value.code == _DESERIALIZATION_ERROR
    where = f"getblocktemplate at {client.url}: "
    assert excinfo.value.args[0].startswith(where)
    assert "Block decode failed" in excinfo.value.args[0].removeprefix(where)


def _block_3(node: NodeAdapter, block_0_height: int, txlist: Sequence[Tx]) -> Block:
    """Return Core's own `block_3`, on `block_2`, carrying `txlist`.

    Timed one second past `block_2`'s own median time, where Core's is
    one second past `block_1`'s: this module's own docstring has why.
    """
    block_2_hash = node.rpc.call("getblockhash", [block_0_height + 2])
    block_2 = node.rpc.call("getblock", [block_2_hash])
    return _create_block(
        bytes.fromhex(block_2_hash),
        block_0_height + 3,
        block_2["mediantime"] + 1,
        txlist,
    )


def a_proposed_block_is_checked_and_not_stored(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.BLOCK_PROPOSAL, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    rpc = node.rpc
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY)

    block_0_height = rpc.call("getblockcount")
    wallet.generate(1)
    block_1 = rpc.call("getblock", [rpc.call("getbestblockhash")])
    block_2 = _create_block(
        bytes.fromhex(block_1["hash"]), block_0_height + 2, block_1["mediantime"] + 1
    )

    # a valid block
    _assert_template(rpc, block_2, None)

    # a bad input hash for the coinbase transaction
    bad_block = copy.deepcopy(block_2)
    prevout = bad_block.transactions[0].vin[0].prev_out
    bad_block.transactions[0].vin[0].prev_out = OutPoint(
        _plus(prevout.tx_id, 1), prevout.vout
    )
    _assert_template(rpc, bad_block, "bad-cb-missing")

    # a block with no transactions
    no_tx_block = copy.deepcopy(block_2)
    no_tx_block.transactions.clear()
    no_tx_block.header.merkle_root = _uint256(0)
    _solve(no_tx_block)
    _assert_template(rpc, no_tx_block, "bad-blk-length", rehash=False)

    # a truncated final transaction
    _decode_failed(node, block_2.serialize(check_validity=False)[:-1].hex())

    # a duplicate transaction
    bad_block = copy.deepcopy(block_2)
    bad_block.transactions.append(bad_block.transactions[0])
    _assert_template(rpc, bad_block, "bad-txns-duplicate")

    # a transaction that spends from thin air
    bad_block = copy.deepcopy(block_2)
    bad_tx = copy.deepcopy(bad_block.transactions[0])
    bad_tx.vin[0].prev_out = OutPoint(_uint256(255), bad_tx.vin[0].prev_out.vout)
    bad_block.transactions.append(bad_tx)
    _assert_template(rpc, bad_block, "bad-txns-inputs-missingorspent")

    # a non-final transaction
    bad_block = copy.deepcopy(block_2)
    bad_block.transactions[0].lock_time = 2**32 - 1
    _assert_template(rpc, bad_block, "bad-txns-nonfinal")

    # a bad transaction count, immediately after the header
    bad_block_sn = bytearray(block_2.serialize(check_validity=False))
    header_size = len(block_2.header.serialize(check_validity=False))
    assert bad_block_sn[header_size] == 1
    bad_block_sn[header_size] += 1
    _decode_failed(node, bad_block_sn.hex())

    # extremely high bits, and bits lowered by one
    bad_block = copy.deepcopy(block_2)
    bad_block.header.bits = _EXTREMELY_HIGH_BITS.to_bytes(4, "big")
    _assert_template(
        rpc, bad_block, "bad-diffbits", solve=False, expect_submit="high-hash"
    )
    bad_block = copy.deepcopy(block_2)
    lowered = int.from_bytes(bad_block.header.bits, "big") - 1
    bad_block.header.bits = lowered.to_bytes(4, "big")
    _assert_template(rpc, bad_block, "bad-diffbits")

    # a bad merkle root
    bad_block = copy.deepcopy(block_2)
    bad_block.header.merkle_root = _plus(bad_block.header.merkle_root, 1)
    _assert_template(rpc, bad_block, "bad-txnmrklroot", rehash=False)

    # bad timestamps
    bad_block = copy.deepcopy(block_2)
    bad_block.header.time = datetime.fromtimestamp(2**32 - 1, UTC)
    _assert_template(rpc, bad_block, "time-too-new")
    bad_block.header.time = datetime.fromtimestamp(0, UTC)
    _assert_template(rpc, bad_block, "time-too-old")

    # a block must build on the current tip
    bad_block = copy.deepcopy(block_2)
    bad_block.header.previous_block_hash = _uint256(123)
    _solve(bad_block)
    _assert_template(
        rpc,
        bad_block,
        "inconclusive-not-best-prevblk",
        expect_submit="prev-blk-not-found",
    )

    # no proof-of-work is needed, and it is accepted when there
    target = int.from_bytes(block_2.header.target, "big")
    # not meeting the target by coincidence
    while _hash_int(block_2) <= target:
        block_2.header.nonce += 1
    _assert_template(rpc, block_2, None)
    _solve(block_2)
    _assert_template(rpc, block_2, None)

    # no proposal submitted a block, and submitting this one succeeds
    assert rpc.call("getblockcount") == block_0_height + 1
    assert rpc.call("submitblock", [_hex(block_2)]) is None
    rpc.call("waitforblockheight", [block_0_height + 2])

    # a block template with a transaction
    tx = wallet.create_self_transfer()
    block_3 = _block_3(node, block_0_height, [tx])
    assert len(block_3.transactions) == 2
    _add_witness_commitment(block_3)
    _solve(block_3)
    _assert_template(rpc, block_3, None)
    # checking it did not update the UTXO set
    _assert_template(rpc, block_3, None)

    # a transaction that spends too much
    bad_tx = copy.deepcopy(tx)
    bad_tx.vout[0] = TxOut(
        _OVERSPENT_VALUE, bad_tx.vout[0].script_pub_key, check_validity=False
    )
    bad_tx_hex = bad_tx.serialize(True, check_validity=False).hex()
    answer = rpc.call("testmempoolaccept", [[bad_tx_hex]])
    assert answer[0]["reject-reason"] == "bad-txns-in-belowout"
    block_3 = _block_3(node, block_0_height, [bad_tx])
    assert len(block_3.transactions) == 2
    _add_witness_commitment(block_3)
    _solve(block_3)
    _assert_template(rpc, block_3, "bad-txns-in-belowout")

    # coins cannot be spent twice
    tx_hex = tx.serialize(True, check_validity=False).hex()
    tx_2 = copy.deepcopy(tx)
    tx_2_hex = tx_2.serialize(True, check_validity=False).hex()
    # nothing wrong with either alone
    assert rpc.call("testmempoolaccept", [[tx_hex]])[0]["allowed"] is True
    assert rpc.call("testmempoolaccept", [[tx_2_hex]])[0]["allowed"] is True
    # but they cannot be combined
    answer = rpc.call("testmempoolaccept", [[tx_hex, tx_2_hex]])
    assert answer[0]["package-error"] == "package-contains-duplicates"
    block_3 = _block_3(node, block_0_height, [tx, tx_2])
    assert len(block_3.transactions) == 3
    _add_witness_commitment(block_3)
    _assert_template(rpc, block_3, "bad-txns-inputs-missingorspent", submit=False)

    # proposals checked from many threads at once
    def check_blocks(_: int) -> None:
        client = node.rpc
        for _ in range(_CHECKS_PER_THREAD):
            _assert_template(
                client, block_3, "bad-txns-inputs-missingorspent", submit=False
            )

    with ThreadPoolExecutor(max_workers=_THREADS) as threads:
        list(threads.map(check_blocks, range(_THREADS)))
