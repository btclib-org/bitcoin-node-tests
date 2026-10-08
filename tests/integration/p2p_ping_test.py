# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ping`, one body over either node.

Read from Core's `test/functional/p2p_ping.py` (`fa5f29774872`,
2025-12-16), the option, clock and log families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a peer that never answers the node's own `ping` is pinged once
connected, a `pong` cancels that ping or not according to its payload,
`getpeerinfo`'s `pingtime`, `minping` and `pingwait` report what the
node's own clock (`Capability.CLOCK`) measured, and the peer is dropped
once a ping goes unanswered past `TIMEOUT_INTERVAL` (`src/net.h`). The
node runs Core's own `-peertimeout=1` (`Capability.PEER_TIMEOUT`).

Each fact of Core's own `run_test` is given the half it is observable
in, the log family's own rule (issue #5): the wire half is every step
with its `getpeerinfo` check and the closing disconnect, and the log half
the same steps with Core's own `pong peer=0: ...` and `ping timeout`
lines asserted around them (`Capability.DEBUG_LOG`). The peer is the
node's first, each test starting its own node, as Core's `peer=0`
presumes. The node is started with the two settings Core's harness
gives every node and `BitcoindAdapter` does not, `-v2transport=0` and
`-connect=0`, `p2p_timeouts_test.py`'s own docstring having why each
is there.

Core's `NodeNoPong` leaves every `ping` unanswered, overriding the
answer `P2PInterface` gives from its background thread. `Peer` answers
one only inside `wait_for`, which `handshake` and `Peer.sync_with_ping`
read through, so this reads through `receive` instead: `_sync_with_ping`
below is Core's `sync_with_ping` barrier that leaves the node's own
`ping` unanswered in `last_message`, as `NodeNoPong` leaves it. Core's
`msg_generic(b"pong", b"")`, a `pong` with no nonce at all, is a
`btclib.p2p.Message` framed by hand.

`p2p_ping_bitcoind_test.py` and `p2p_ping_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import contextlib
import secrets
import time
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import Message, Ping, Pong

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "ping_replies_are_logged",
    "ping_replies_are_reported_on_rpc",
]

# Core's own constants, `src/net_processing.cpp`'s and `src/net.h`'s
_PING_INTERVAL = 2 * 60
_TIMEOUT_INTERVAL = 20 * 60

# Core's own `extra_args`, and what its harness gives every node
_EXTRA_ARGS = ("-peertimeout=1", "-v2transport=0", "-connect=0")


def _read_until(peer: Peer, command: str, nonce: int | None = None) -> None:
    """Read, answering nothing, until a `command` message arrives.

    :param peer: the connection to read.
    :param command: the message to stop at.
    :param nonce: where given, the nonce a `pong` must carry to stop at.
    """
    while True:
        message = peer.receive()
        if message.command != command:
            continue
        if nonce is None or Pong.parse(message.payload).nonce == nonce:
            return


def _sync_with_ping(peer: Peer) -> None:
    """Core's `sync_with_ping`, leaving the node's own `ping` unanswered.

    `Peer.sync_with_ping`'s own pair of pings, read for through `receive`
    rather than `wait_for`: a `ping` the node sends meanwhile is kept in
    `last_message` and never answered.
    """
    nonce = secrets.randbelow(2**64 - 1) + 1
    peer.send(Ping(0))
    peer.send(Ping(nonce))
    _read_until(peer, "pong", nonce)


def _wait_for_ping(peer: Peer) -> int:
    """Return the nonce of the node's own pending `ping`, reading for one.

    Core's `wait_until(lambda: 'ping' in no_pong_node.last_message)`
    followed by its `pop`: the `ping` is consumed, so the next call waits
    for the next one.
    """
    if "ping" not in peer.last_message:
        _read_until(peer, "ping")
    return Ping.parse(peer.last_message.pop("ping").payload).nonce


def _check_peer_info(
    node: NodeAdapter,
    *,
    pingtime: float | None,
    minping: float | None,
    pingwait: float | None,
) -> None:
    """Core's `check_peer_info`: the three fields, absent where `None`."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    stats = peers[0]
    assert stats.get("pingtime") == pingtime
    assert stats.get("minping") == minping
    assert stats.get("pingwait") == pingwait


def _ping_pong(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
    *,
    logged: bool,
) -> None:
    """Run Core's own `run_test`, asserting its log lines where `logged`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :param logged: whether to require `Capability.DEBUG_LOG` and assert
        Core's own lines around each step.
    :raises TypeError: `logged`, and the node declares
        `Capability.DEBUG_LOG` without being the adapter that names a
        `debug_log_path`.
    """
    (node,) = cluster(1)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    if logged:
        require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
        if not isinstance(node, BitcoindAdapter):
            err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
            raise TypeError(err_msg)
        log_path = node.debug_log_path

    def expect(lines: list[str]) -> AbstractContextManager[None]:
        """Return Core's `assert_debug_log` over `lines`, or no check."""
        if logged:
            return assert_debug_log(log_path, lines)
        return contextlib.nullcontext()

    node.restart(_EXTRA_ARGS)
    magic = magic_from_chain(node.chain)
    mock_time = int(time.time())

    def mock_forward(delta: int) -> None:
        nonlocal mock_time
        mock_time += delta
        node.set_mock_time(mock_time)

    mock_forward(0)
    with Peer(node.p2p_address, magic) as peer:
        # a ping is sent once the connection is established
        peer.handshake()
        _sync_with_ping(peer)
        mock_forward(3)
        assert _wait_for_ping(peer) != 0
        _check_peer_info(node, pingtime=None, minping=None, pingwait=3)

        # a reply without a nonce cancels the ping
        with expect(["pong peer=0: Short payload"]):
            peer.send_raw(Message(magic, "pong", b"").serialize())
            _sync_with_ping(peer)
        _check_peer_info(node, pingtime=None, minping=None, pingwait=None)

        # a reply without a ping
        with expect(
            [
                (
                    "pong peer=0: Unsolicited pong without ping, "
                    "0 expected, 0 received, 8 bytes"
                )
            ]
        ):
            peer.send(Pong(0))
            _sync_with_ping(peer)
        _check_peer_info(node, pingtime=None, minping=None, pingwait=None)

        # a reply with the wrong nonce does not cancel the ping
        assert "ping" not in peer.last_message
        with expect(["pong peer=0: Nonce mismatch"]):
            mock_forward(_PING_INTERVAL + 1)
            nonce = _wait_for_ping(peer)
            mock_forward(9)
            peer.send(Pong(nonce - 1))
            _sync_with_ping(peer)
        _check_peer_info(node, pingtime=None, minping=None, pingwait=9)

        # a reply with a zero nonce does cancel the ping
        with expect(["pong peer=0: Nonce zero"]):
            peer.send(Pong(0))
            _sync_with_ping(peer)
        _check_peer_info(node, pingtime=None, minping=None, pingwait=None)

        # the round trip is reported on RPC, minping falling after a faster one
        for ping_delay in (29, 9):
            assert "ping" not in peer.last_message
            mock_forward(_PING_INTERVAL + 1)
            _read_until(peer, "ping")
            mock_forward(ping_delay)
            peer.send(Pong(_wait_for_ping(peer)))
            _sync_with_ping(peer)
            _check_peer_info(
                node, pingtime=ping_delay, minping=ping_delay, pingwait=None
            )

        # the peer is dropped once a ping goes unanswered past the timeout
        assert "ping" not in peer.last_message
        node.rpc.call("ping")
        _wait_for_ping(peer)
        with expect(["ping timeout: 1201.000000s"]):
            mock_forward(_TIMEOUT_INTERVAL // 2)
            # a ping of the peer's own does not stop the disconnect
            _sync_with_ping(peer)
            mock_forward(_TIMEOUT_INTERVAL // 2 + 1)
            peer.wait_for_disconnect()


def ping_replies_are_reported_on_rpc(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check the wire half: `getpeerinfo` after each reply, and the drop.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _ping_pong(cluster, skip_counts, logged=False)


def ping_replies_are_logged(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check the log half: Core's own lines, around the same steps.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _ping_pong(cluster, skip_counts, logged=True)
