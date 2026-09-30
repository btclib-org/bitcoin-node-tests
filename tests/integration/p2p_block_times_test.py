# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_block_times`, as a body over either node.

Read from Core's `test/functional/p2p_block_times.py` (`5d5397d84108`,
2026-07-25): `getpeerinfo`'s `last_block_announcement` for an outbound
full-relay peer is zero until the peer is the first to announce a block
extending the node's tip, is then the node's clock, and moves neither
for a second announcement of that block nor for a block at the same
height with no more work.

The body has the node dial the peer (`Capability.TYPED_OUTBOUND`), sets
the node's clock as Core's does (`Capability.CLOCK`), and mines the block
Core's own mines to leave initial block download (`Capability.MINE`).
Core's `P2PDataStore` answers the node's `getdata` from its framework's
network thread; here the peer waits for the `getdata` naming the block
and sends it, which is what `send_blocks_and_test` waits for before its
own `ping` round trip. `P2PDataStore` answers a `getheaders` from its
store too, and this peer answers none: the node's `getheaders` is read
before `_add_outbound` returns, ahead of any block in the store.

`getpeerinfo` reports `last_block_announcement` only past the pinned
release, from bitcoin/bitcoin#27052's merge. Where the build's own
`getnetworkinfo` `version` reads older
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)),
the body asserts the field absent at each of Core's checks of it, and
keeps Core's `last_block` check. The constant's own comment has the
known limit.

Core's harness starts every node with a `peertimeout`
(`write_config`, `test_framework/util.py`) and this port passes none:
the body moves the node's clock a second past the wall clock, far short
of the twenty minutes `CConnman::InactivityCheck` (`src/net.cpp`) waits.

`p2p_block_times_bitcoind_test.py` and
`p2p_block_times_btclib_node_test.py` run the body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import BlockPayload, GetData, Headers
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Listener

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from bitcoin_node_tests.peer import Peer

__all__ = ["block_announcement_time_is_tracked"]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# `OP_TRUE`, what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"

# Core's own `create_block` default: the wall clock ten minutes ahead
_BLOCK_TIME_AHEAD = 600

# Core's own default wait, `P2PInterface`'s and `wait_until`'s
_WAIT = 60.0

# Core's own `CLIENT_VERSION` (`src/clientversion.h`), the running build's
# own `getnetworkinfo` `version`, at or past which `getpeerinfo` reports
# `last_block_announcement`: `32.99`'s, bitcoin/bitcoin#27052 having
# merged (`71c30b6083`, 2026-09-22) after the version moved to `32.99`
# (`f3fec67c3e`, 2026-09-11) and neither `v32.0rc1` nor `v32.0rc2`
# carrying it. A known limit: a `master` build between those two merges
# reports `329900` and no such field, so this test fails against such a
# build
_LAST_BLOCK_ANNOUNCEMENT_VERSION = 329900


def _block(previous: bytes, height: int, block_time: int) -> Block:
    """Core's own `create_block(previous, create_coinbase(height), ...)`."""
    coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
    candidate = build_block(
        previous,
        [coinbase],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(candidate.header)
    assert solved is not None
    return Block(solved, candidate.transactions, check_validity=False)


def _add_outbound(node: NodeAdapter) -> Peer:
    """Have `node` dial a fresh listener as full relay, and shake hands."""
    with Listener(_MAGIC) as listener:
        node.add_outbound_connection(listener.address, "outbound-full-relay")
        peer = listener.accept()
    try:
        peer.handshake()
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer


def _headers(block: Block) -> Headers:
    """Core's own `msg_headers([CBlockHeader(block)])`, a regtest header."""
    return Headers([block.header], check_validity=False)


def _asks_for(block_hash: bytes) -> Callable[[Message], bool]:
    """Return whether a `getdata` names `block_hash`."""

    def predicate(message: Message) -> bool:
        return any(
            item.hash == block_hash for item in GetData.parse(message.payload).items
        )

    return predicate


def _send_block_and_test(peer: Peer, node: NodeAdapter, block: Block) -> None:
    """Core's own `send_blocks_and_test([block], node, success=True)`."""
    block_hash = block.header.hash
    peer.send(_headers(block), check_validity=False)
    peer.wait_for("getdata", predicate=_asks_for(block_hash), timeout=_WAIT)
    peer.send(
        BlockPayload(block, include_witness=True, check_validity=False),
        check_validity=False,
    )
    peer.sync_with_ping(timeout=_WAIT)
    wait_until(
        lambda: node.rpc.call("getbestblockhash") == block_hash.hex(), timeout=_WAIT
    )


def _reports_announcement(node: NodeAdapter) -> bool:
    """Whether `node`'s `getpeerinfo` reports `last_block_announcement`.

    Core's own claim for every node, bitcoind before
    `_LAST_BLOCK_ANNOUNCEMENT_VERSION` excepted, read off its own
    `getnetworkinfo` `version`
    ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
    """
    if not isinstance(node, BitcoindAdapter):
        return True
    version = node.rpc.call("getnetworkinfo")["version"]
    return bool(version >= _LAST_BLOCK_ANNOUNCEMENT_VERSION)


def _peer_info(node: NodeAdapter) -> dict[str, object]:
    """Return `getpeerinfo`'s entry for the node's only peer."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    (peer_info,) = peers
    assert isinstance(peer_info, dict)
    return peer_info


def _assert_last_announcement(node: NodeAdapter, expected: int) -> None:
    """Assert `last_block_announcement`, or its absence on an older build."""
    peer_info = _peer_info(node)
    if _reports_announcement(node):
        assert peer_info["last_block_announcement"] == expected
    else:
        assert "last_block_announcement" not in peer_info


def block_announcement_time_is_tracked(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `run_test`: a first announcement alone sets the time.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)

    cur_time = int(time.time())
    node.set_mock_time(cur_time)
    # one block to leave initial block download
    node.mine(1)

    with _add_outbound(node) as peer:
        # the peer's own block at height two
        tip = bytes.fromhex(str(node.rpc.call("getbestblockhash")))
        block = _block(tip, 2, int(time.time()) + _BLOCK_TIME_AHEAD)

        # zero before any announcement
        _assert_last_announcement(node, 0)

        _send_block_and_test(peer, node, block)

        # the node's clock, for the block and for its announcement
        assert _peer_info(node)["last_block"] == cur_time
        _assert_last_announcement(node, cur_time)

        # an announcement of no new block moves nothing
        node.set_mock_time(cur_time + 1)
        peer.send(_headers(block), check_validity=False)
        peer.sync_with_ping(timeout=_WAIT)
        _assert_last_announcement(node, cur_time)

        # nor does a second block at height two, its work no greater
        block_time = int(block.header.time.timestamp()) + 1
        block2 = _block(tip, 2, block_time)
        peer.send(_headers(block2), check_validity=False)
        peer.sync_with_ping(timeout=_WAIT)
        _assert_last_announcement(node, cur_time)
