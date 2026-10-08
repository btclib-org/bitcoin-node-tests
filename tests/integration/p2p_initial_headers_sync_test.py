# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_initial_headers_sync`, as bodies over either node.

Read from Core's `test/functional/p2p_initial_headers_sync.py`
(`fa4cb96bdec2`, 2026-02-17): a node still at genesis asks one peer for
headers, and each block announced by every peer adds one more peer it
asks; then a stalling first peer is dropped once the headers download
times out, unless it holds the `noban` permission, which keeps it
connected and has the node ask a peer again.

The first check dials the node alone and asks for no capability. Each
timeout check has the node dial an outbound peer, which is what lets the
node drop its only headers peer, and moves the clock past the timeout, so
it asks for `Capability.TYPED_OUTBOUND` and `Capability.CLOCK`, and for
`Capability.PEER_TIMEOUT` besides: its node is restarted with settings
Core's own harness gives every node, `_EXTRA_ARGS` below. Each is a
wire half and a log half, the log family's own split (issue #5), the log
half asking for `Capability.DEBUG_LOG` besides.

What differs from Core's file:

- each check runs over a fresh node, where Core restarts one;
- a peer reads what the node sent only when the test reads its socket, so
  every peer round-trips a `ping` before the count of peers sent a
  `getheaders` is taken;
- the `noban` check's `-whitelist` asks for no capability, as
  `rpc_setban.py`'s own `noban` row does not.

`p2p_initial_headers_sync_bitcoind_test.py` and
`p2p_initial_headers_sync_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import math
import secrets
import time
from contextlib import nullcontext
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import GetHeaders, Headers, Inv, Inventory, InventoryType

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Listener, Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "headers_are_asked_of_one_peer_per_announcement",
    "headers_timeout_drops_the_peer",
    "headers_timeout_is_logged",
    "headers_timeout_keeps_a_noban_peer",
    "headers_timeout_of_a_noban_peer_is_logged",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# what Core's own harness starts every node with and `BitcoindAdapter`
# does not: `write_config`'s (`test_framework/util.py`) `peertimeout`, so
# that moving the clock past the headers timeout does not also drop every
# peer as inactive, and `connect=0`, so that it opens no connection of
# its own once the clock has moved
_EXTRA_ARGS = ("-peertimeout=999999999", "-connect=0")

# the id a restarted node gives the first peer it holds
_FIRST_PEER_ID = 0

# Core's own constants of `net_processing.cpp`, restated by its test
_HEADERS_DOWNLOAD_TIMEOUT_BASE_SEC = 15 * 60
_HEADERS_DOWNLOAD_TIMEOUT_PER_HEADER_MS = 1
_POW_TARGET_SPACING_SEC = 10 * 60


def _calculate_headers_timeout(best_header_time: int, current_time: int) -> int:
    """Core's `calculate_headers_timeout`: never below the node's own."""
    seconds_since_best_header = current_time - best_header_time
    variable_timeout_sec = math.ceil(
        _HEADERS_DOWNLOAD_TIMEOUT_PER_HEADER_MS
        / 1_000
        * seconds_since_best_header
        / _POW_TARGET_SPACING_SEC
    )
    return int(current_time + _HEADERS_DOWNLOAD_TIMEOUT_BASE_SEC + variable_timeout_sec)


def _add_inbound(node: NodeAdapter) -> Peer:
    """Dial `node`, and shake hands: Core's `add_p2p_connection`."""
    peer = Peer(node.p2p_address, magic_from_chain(node.chain))
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _add_outbound(node: NodeAdapter) -> Peer:
    """Have `node` dial a fresh listener as full relay, and shake hands."""
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, "outbound-full-relay")
        peer = listener.accept()
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _starts_at(block_hash: bytes) -> Callable[[object], bool]:
    """Return whether a `getheaders` locator starts at `block_hash`."""

    def predicate(message: object) -> bool:
        payload = getattr(message, "payload", b"")
        return GetHeaders.parse(payload).locator[0] == block_hash

    return predicate


def _wait_for_getheaders(peer: Peer, block_hash: bytes) -> None:
    """Core's `wait_for_getheaders`: take the latest, or wait for the next.

    Core pops the latest `getheaders` already received before waiting,
    so a later wait on the same peer asks for a new one.
    """
    last = peer.last_message.pop("getheaders", None)
    if last is not None and _starts_at(block_hash)(last):
        return
    peer.wait_for("getheaders", predicate=_starts_at(block_hash))
    peer.last_message.pop("getheaders")


def _best_hash(node: NodeAdapter) -> bytes:
    """Return `node`'s own tip hash, in the order a `getheaders` carries it."""
    return bytes.fromhex(str(node.rpc.call("getbestblockhash")))


def _announce_random_block(peers: Sequence[Peer]) -> None:
    """Core's `announce_random_block`: an `inv` of a block nobody has."""
    inv = Inv([Inventory(InventoryType.MSG_BLOCK, secrets.token_bytes(32))])
    for peer in peers:
        peer.send(inv)
        peer.sync_with_ping()


def _getheaders_recipients(peers: Sequence[Peer]) -> list[Peer]:
    """Return the peers holding a `getheaders` not yet waited for."""
    return [peer for peer in peers if "getheaders" in peer.last_message]


def headers_are_asked_of_one_peer_per_announcement(cluster: _Cluster) -> None:
    """Check headers are asked of one peer, then one more per announcement.

    Over a fresh node, its chain at genesis: a node whose best header is
    less than a day old asks every peer, and the session's own shared
    node may have mined.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    """
    (adapter,) = cluster(1)
    best_hash = _best_hash(adapter)
    peers: list[Peer] = []
    try:
        peer1 = _add_inbound(adapter)
        peers.append(peer1)
        _wait_for_getheaders(peer1, best_hash)
        # an empty answer clears the request, so peer1 can be asked again
        peer1.send(Headers())

        peer2 = _add_inbound(adapter)
        peers.append(peer2)
        peer3 = _add_inbound(adapter)
        peers.append(peer3)
        for peer in peers:
            peer.sync_with_ping()
        assert _getheaders_recipients([peer2, peer3]) == []

        _announce_random_block(peers)
        _wait_for_getheaders(peer1, best_hash)
        peer1.send(Headers())
        recipients = _getheaders_recipients([peer2, peer3])
        assert len(recipients) == 1
        recipients[0].send(Headers())

        _announce_random_block(peers)
        _wait_for_getheaders(peer1, best_hash)
        (remaining,) = (peer for peer in (peer2, peer3) if peer is not recipients[0])
        _wait_for_getheaders(remaining, best_hash)
    finally:
        for peer in peers:
            peer.close()


def _debug_log(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> Path:
    """Return the log a log half reads, or skip where the node keeps none.

    :raises TypeError: `adapter` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
    if not isinstance(adapter, BitcoindAdapter):
        err_msg = f"{type(adapter).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return adapter.debug_log_path


def _expecting(
    log_path: Path | None, expected: Sequence[str]
) -> AbstractContextManager[None]:
    """Return `assert_debug_log` over `log_path`, or nothing for a wire half."""
    if log_path is None:
        return nullcontext()
    return assert_debug_log(log_path, expected)


def _setup_timeout_test_peers(
    node: NodeAdapter, log_path: Path | None
) -> tuple[Peer, Peer]:
    """Core's `setup_timeout_test_peers`: an inbound sync peer, an outbound one.

    The outbound peer is what lets the node drop its sync peer at all:
    the timeout disconnects only a sync peer the node has others beside.
    The inbound peer is the first the restarted node holds, so its id is
    `_FIRST_PEER_ID`, which Core's own expected lines name too.

    :returns: the inbound peer and the outbound one.
    """
    best_hash = _best_hash(node)
    expected = f"initial getheaders (0) to peer={_FIRST_PEER_ID}"
    peer1 = Peer(node.p2p_address, magic_from_chain(node.chain))
    try:
        with _expecting(log_path, [expected]):
            peer1.handshake()
            _wait_for_getheaders(peer1, best_hash)
        peer2 = _add_outbound(node)
    except BaseException:
        peer1.close()
        raise
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert len(peers) == 2
    return peer1, peer2


def _trigger_headers_timeout(node: NodeAdapter, mock_time: int) -> None:
    """Core's `trigger_headers_timeout`: the clock one second past it.

    The node has no header past genesis, so the best header's time is the
    tip's, `getblockchaininfo`'s own `time`.
    """
    info = node.rpc.call("getblockchaininfo")
    assert isinstance(info, dict)
    timeout = _calculate_headers_timeout(int(info["time"]), mock_time)
    node.set_mock_time(timeout + 1)


def _check_headers_timeout(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's `test_normal_peer_timeout`, the node fresh rather than restarted.

    :param log_path: the node's own log where the check is a log half.
    """
    node.restart(_EXTRA_ARGS)
    mock_time = int(time.time())
    node.set_mock_time(mock_time)
    peer1, peer2 = _setup_timeout_test_peers(node, log_path)
    with peer1, peer2:
        expected = f"Timeout downloading headers, disconnecting peer={_FIRST_PEER_ID}"
        with _expecting(log_path, [expected]):
            _trigger_headers_timeout(node, mock_time)
            peer1.wait_for_disconnect()
            wait_until(lambda: len(node.rpc.call("getpeerinfo")) == 1)
        _wait_for_getheaders(peer2, _best_hash(node))


def _check_noban_headers_timeout(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's `test_noban_peer_timeout`, the node fresh rather than restarted.

    :param log_path: the node's own log where the check is a log half.
    """
    node.restart([*_EXTRA_ARGS, "-whitelist=noban@127.0.0.1"])
    mock_time = int(time.time())
    node.set_mock_time(mock_time)
    peer1, peer2 = _setup_timeout_test_peers(node, log_path)
    with peer1, peer2:
        expected = (
            "Timeout downloading headers from noban peer, "
            f"not disconnecting peer={_FIRST_PEER_ID}"
        )
        with _expecting(log_path, [expected]):
            _trigger_headers_timeout(node, mock_time)
            peer1.sync_with_ping()
            peers = node.rpc.call("getpeerinfo")
            assert isinstance(peers, list)
            assert len(peers) == 2
        wait_until(lambda: _recipients_after_ping([peer1, peer2]) != [])
        assert len(_getheaders_recipients([peer1, peer2])) == 1


def _recipients_after_ping(peers: Sequence[Peer]) -> list[Peer]:
    """Ping every peer in turn, then return those asked for headers."""
    for peer in peers:
        peer.sync_with_ping()
    return _getheaders_recipients(peers)


def headers_timeout_drops_the_peer(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the wire half: a stalling sync peer is dropped at the timeout.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    _check_headers_timeout(node, None)


def headers_timeout_is_logged(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the log half: the initial `getheaders`, then the timeout's drop.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    _check_headers_timeout(node, _debug_log(node, skip_counts))


def headers_timeout_keeps_a_noban_peer(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: a `noban` sync peer is kept, one peer asked again.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    _check_noban_headers_timeout(node, None)


def headers_timeout_of_a_noban_peer_is_logged(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: the timeout of a `noban` peer, not dropping it.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    _check_noban_headers_timeout(node, _debug_log(node, skip_counts))
