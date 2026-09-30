# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_block`, as bodies over either node.

Read from Core's `test/functional/p2p_invalid_block.py` (`fa16bc53d79c`,
2026-04-16): a node takes a valid block from a peer, refuses a block
whose duplicated transaction leaves its merkle root unchanged
(CVE-2012-2459) and then takes the original block under that same hash,
refuses a transaction spending one output twice (CVE-2018-17144) whether
that output is in the same block or an earlier one, refuses a coinbase
paying more than the subsidy, and refuses a block more than
`MAX_FUTURE_BLOCK_TIME` ahead of its clock, taking the same block once
its clock has moved a second on.

Core's run is one sequence over one node, and each body is that whole
sequence over a fresh node, each block's acceptance or refusal read off
`getbestblockhash` as Core's `send_blocks_and_test` reads it. The log
half asserts besides the reject reason Core's `reject_reason` asserts in
the node's own log, around each refused block (`Capability.DEBUG_LOG`).
Each body asks for `Capability.MINE`, the node mining the blocks that
mature the first coinbase, and `Capability.CLOCK`, for the step ahead
of the node's clock.

Each block is built with btclib in the shape of Core's own
`create_block` and `create_coinbase` (`blocktools.py`), its coinbase
paying `OP_TRUE`, and each spend is Core's own `create_tx_with_script`:
an `OP_TRUE` scriptSig and an empty scriptPubKey. Core's `P2PDataStore`
answers the node's `getdata` from its framework's network thread; here
the peer sends the block once the node's `getdata` naming it arrives,
which is what `send_blocks_and_test` waits for before its own `ping`
round trip. A round trip that fails is a peer the node dropped, which
Core's own round trip fails on too.

What differs from Core's file:

- the node is restarted with the `-whitelist=noban,in,out@127.0.0.1`
  that Core's `noban_tx_relay` starts it with, the permission that keeps
  the peer connected through the refusals; it asks for no capability,
  as `p2p_initial_headers_sync_test.py`'s own `noban` check does not;
- the `getdata` the node sends for the mutated block's hash once it has
  refused that block is awaited ahead of the ping round trip that would
  read past it, and the original block is later sent as its answer.
  Core's `P2PDataStore` answers each request from its store as it
  arrives and records every hash it was asked for, so its own wait for
  the original block's `getdata` is met by a request already recorded
  under that hash.

`p2p_invalid_block_bitcoind_test.py` and
`p2p_invalid_block_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from contextlib import nullcontext
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.block.block import Block, merkle_root_and_mutated_from_transactions
from btclib.block.build import build_coinbase
from btclib.block.limits import MAX_FUTURE_BLOCK_TIME
from btclib.block.mining import candidate_block_header, mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import BlockPayload, GetData, Headers
from btclib.p2p.magic import magic_from_chain
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY, SEQUENCE_FINAL

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager
    from pathlib import Path

    from btclib.p2p import Message

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["invalid_blocks_are_logged", "invalid_blocks_are_refused"]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# Core's own `COIN` (`test_framework/messages.py`)
_COIN = 100_000_000

# `OP_TRUE`: what Core's own `create_coinbase` pays, and the scriptSig of
# each of its `create_tx_with_script` spends
_OP_TRUE = b"\x51"

# what Core's own `noban_tx_relay` adds to every node's start
_NOBAN = "-whitelist=noban,in,out@127.0.0.1"

# Core's own default wait, `send_blocks_and_test`'s, and the shorter one
# it gives the original block after its mutated copy
_WAIT = 60.0
_ORIGINAL_WAIT = 5.0


def _debug_log(
    node: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> Path:
    """Return the log the log half reads, or skip where the node keeps none.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def _expecting(
    log_path: Path | None, reject_reason: str | None
) -> AbstractContextManager[None]:
    """Return `assert_debug_log` over `log_path`, or nothing to assert.

    Core's own `send_blocks_and_test` asserts its `reject_reason` alone,
    and nothing for a block it expects taken.
    """
    if log_path is None or reject_reason is None:
        return nullcontext()
    return assert_debug_log(log_path, [reject_reason])


def _create_block(
    previous: bytes,
    height: int,
    block_time: int,
    transactions: Sequence[Tx] = (),
    *,
    coinbase_value: int | None = None,
) -> Block:
    """Core's own `create_block`, over `create_coinbase(height, nValue=...)`.

    Solved, and built without asking its transactions to be valid: the
    refused blocks carry a spend of one output twice.

    :param coinbase_value: what the coinbase pays, in satoshi, where not
        the subsidy at `height`.
    """
    coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
    if coinbase_value is not None:
        coinbase.vout[0] = TxOut(coinbase_value, _OP_TRUE)
    carried = [coinbase, *transactions]
    header = candidate_block_header(
        previous,
        carried,
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(header)
    assert solved is not None
    return Block(solved, carried, check_validity=False)


def _spend(previous: Tx, *, duplicate_input: bool = False) -> Tx:
    """Core's own `create_tx_with_script(previous, 0, OP_TRUE, 50 * COIN)`.

    :param duplicate_input: the input appended a second time, Core's own
        `tx.vin.append(tx.vin[0])`.
    """
    tx_in = TxIn(OutPoint(previous.id, 0), _OP_TRUE, SEQUENCE_FINAL)
    return Tx(
        2,
        0,
        [tx_in, tx_in] if duplicate_input else [tx_in],
        [TxOut(50 * _COIN, b"")],
        check_validity=False,
    )


def _asks_for(block_hash: bytes) -> Callable[[Message], bool]:
    """Return whether a `getdata` names `block_hash`."""

    def predicate(message: Message) -> bool:
        items = GetData.parse(message.payload, check_validity=False).items
        return any(item.hash == block_hash for item in items)

    return predicate


def _block_payload(block: Block) -> BlockPayload:
    """Core's own `msg_block(block)`."""
    return BlockPayload(block, include_witness=True, check_validity=False)


def _send_blocks_and_test(
    peer: Peer,
    node: NodeAdapter,
    block: Block,
    log_path: Path | None,
    *,
    reject_reason: str | None = None,
    force_send: bool = False,
    asked: bool = False,
    asked_again: bool = False,
    timeout: float = _WAIT,
) -> None:
    """Core's own `send_blocks_and_test([block], node, ...)`, one block.

    The block is taken where `reject_reason` is `None`, and refused with
    that reason otherwise, the reason asserted in `log_path` where given.

    :param force_send: the block sent unasked, Core's own `force_send`,
        rather than its header first and the block once asked for.
    :param asked: the node's `getdata` naming the block already read, the
        block then sent right after its header.
    :param asked_again: the node's `getdata` naming the refused block's
        hash once more awaited, ahead of the ping round trip that would
        read past it.
    """
    block_hash = block.header.hash
    with _expecting(log_path, reject_reason):
        if force_send:
            peer.send(_block_payload(block), check_validity=False)
        else:
            peer.send(Headers([block.header], check_validity=False))
            if not asked:
                peer.wait_for(
                    "getdata", predicate=_asks_for(block_hash), timeout=timeout
                )
            peer.send(_block_payload(block), check_validity=False)
        if asked_again:
            peer.wait_for("getdata", predicate=_asks_for(block_hash), timeout=timeout)
        peer.sync_with_ping(timeout=timeout)
        if reject_reason is None:
            wait_until(
                lambda: node.rpc.call("getbestblockhash") == block_hash.hex(),
                timeout=timeout,
            )
        else:
            assert node.rpc.call("getbestblockhash") != block_hash.hex()


def _best_block(node: NodeAdapter) -> tuple[bytes, int, int]:
    """Return the tip's own hash, and the height and time a child takes."""
    best_hash = node.rpc.call("getbestblockhash")
    best_block = node.rpc.call("getblock", [best_hash])
    return bytes.fromhex(best_hash), best_block["height"] + 1, best_block["time"] + 1


def _connect(node: NodeAdapter) -> Peer:
    """Core's own `add_p2p_connection`: a handshake, then a ping round trip."""
    peer = Peer(node.p2p_address, _MAGIC)
    try:
        peer.handshake()
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer


def _run(node: BitcoindAdapter | BtclibNodeAdapter, log_path: Path | None) -> None:
    """Core's own `run_test`, over `node` already started with `_NOBAN`.

    :param log_path: the node's own log where the body is the log half.
    """
    with _connect(node) as peer:
        tip, height, block_time = _best_block(node)

        # a block paying `OP_TRUE`, its coinbase spent below
        block1 = _create_block(tip, height, block_time)
        _send_blocks_and_test(peer, node, block1, log_path)

        # the coinbase matured
        node.mine(COINBASE_MATURITY)
        tip, height, block_time = _best_block(node)

        # a spend of the coinbase and a spend of that spend
        tx1 = _spend(block1.transactions[0])
        tx2 = _spend(tx1)
        block2_orig = _create_block(tip, height, block_time, [tx1, tx2])
        block_time += 1

        # the last transaction duplicated: the same merkle root, so the
        # same header and the same hash, and a different block
        block2 = Block(
            block2_orig.header,
            [*block2_orig.transactions, tx2],
            check_validity=False,
        )
        merkle_root, _ = merkle_root_and_mutated_from_transactions(block2.transactions)
        assert merkle_root == block2.header.merkle_root
        assert block2.header.hash == block2_orig.header.hash
        assert block2.transactions != block2_orig.transactions
        _send_blocks_and_test(
            peer,
            node,
            block2,
            log_path,
            reject_reason="bad-txns-duplicate",
            asked_again=True,
        )

        # the last transaction spending its one input twice
        tx2_dup = _spend(tx1, duplicate_input=True)
        block2_dup = _create_block(
            tip, height, int(block2_orig.header.time.timestamp()), [tx1, tx2_dup]
        )
        _send_blocks_and_test(
            peer, node, block2_dup, log_path, reject_reason="bad-txns-inputs-duplicate"
        )

        # a coinbase paying twice the subsidy
        block3 = _create_block(tip, height, block_time, coinbase_value=100 * _COIN)
        block_time += 1
        _send_blocks_and_test(
            peer, node, block3, log_path, reject_reason="bad-cb-amount"
        )

        # the original block, under the hash its mutated copy was refused at
        _send_blocks_and_test(
            peer, node, block2_orig, log_path, asked=True, timeout=_ORIGINAL_WAIT
        )
        height += 1
        block_time += 1
        tip = block2_orig.header.hash

        # a spend of an earlier block's output, spending its input twice
        tx3 = _spend(tx2, duplicate_input=True)
        block4 = _create_block(tip, height, block_time, [tx3])
        _send_blocks_and_test(
            peer, node, block4, log_path, reject_reason="bad-txns-inputs-duplicate"
        )

        # a block a second past the node's clock plus the bound, refused
        # unasked for, then taken once the clock has moved a second on
        now = int(time.time())
        node.set_mock_time(now)
        future = _create_block(tip, height, now + MAX_FUTURE_BLOCK_TIME + 1)
        _send_blocks_and_test(
            peer,
            node,
            future,
            log_path,
            reject_reason="time-too-new",
            force_send=True,
        )
        node.set_mock_time(now + 1)
        _send_blocks_and_test(peer, node, future, log_path)


def invalid_blocks_are_refused(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the wire half: each invalid block refused, each valid one taken.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    node.restart([_NOBAN])
    _run(node, None)


def invalid_blocks_are_logged(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the log half: each refusal logged with Core's own reject reason.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    node.restart([_NOBAN])
    _run(node, log_path)
