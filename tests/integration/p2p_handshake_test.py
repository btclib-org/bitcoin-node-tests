# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`, one body per check over either node.

Read from Core's `test/functional/p2p_handshake.py` (`3fd68a95e68b`,
2026-04-07): the first check of its `run_test`, a second `verack` sent
once the handshake is complete. `net_processing.cpp`'s own `VERACK`
branch logs "ignoring redundant verack message" and returns when
`fSuccessfullyConnected` is already set, so the peer stays connected.
Core asserts the log line, and its own `send_and_ping` fails where the
connection closed instead: two facts of one action, each given a half of
its own, the log family's own rule (issue #5). The wire half round-trips
a `ping` after the second `verack`; the log half is bitcoind's own
wording, gated on `Capability.DEBUG_LOG`.

The rest of Core's file has the node dial the test
([ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44)),
each check split the same way and each body over a fresh node:

- an outbound peer offering less than `NODE_NETWORK | NODE_WITNESS` is
  dropped once the node reads its `version`, on each outbound type that
  expects services, and one offering both is kept;
- a `NODE_NETWORK_LIMITED` peer is dropped while the tip is older than a
  day and kept once it is not, the tip mined at a mock time in the past;
- a feeler is dropped once the node reads its `version`;
- a node made to dial its own address drops the connection.

Each dialled peer answers the node's `version` with its own and nothing
else where it expects to be dropped, and shakes hands in full where it
expects to be kept. `p2p_handshake_bitcoind_test.py` and
`p2p_handshake_btclib_node_test.py` run every body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import itertools
import secrets
import time
from contextlib import nullcontext
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import ServiceFlags, Verack, Version

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

__all__ = [
    "feeler_completion_is_logged",
    "feeler_is_dropped_after_its_version",
    "limited_peer_is_kept_only_near_the_tip",
    "limited_peer_refusal_is_logged",
    "outbound_services_decide_the_connection",
    "outbound_services_refusal_is_logged",
    "redundant_verack_is_logged",
    "redundant_verack_keeps_the_connection",
    "self_connection_is_dropped",
    "self_connection_is_logged",
]

_MAGIC = magic_from_chain("regtest")

# the types Core's own `test_desirable_service_flags` dials, those
# `CNode::ExpectServicesFromConn` (`src/net.h`) answers true for
_CONNECTION_TYPES = ("outbound-full-relay", "block-relay-only", "addr-fetch")

# Core's `DESIRABLE_SERVICE_FLAGS_FULL` and `DESIRABLE_SERVICE_FLAGS_PRUNED`
_DESIRABLE_FULL = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS
_DESIRABLE_PRUNED = ServiceFlags.NODE_NETWORK_LIMITED | ServiceFlags.NODE_WITNESS

_ONE_HOUR = 60 * 60

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]


def redundant_verack_keeps_the_connection(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a second `verack` is ignored, not disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Verack())
        peer.sync_with_ping()


def redundant_verack_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for the `verack` it ignored.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    :raises TypeError: `adapter` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
    if not isinstance(adapter, BitcoindAdapter):
        err_msg = f"{type(adapter).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(adapter.debug_log_path, ["ignoring redundant verack message"]),
    ):
        peer.handshake()
        peer.send(Verack())
        peer.sync_with_ping()


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


def _dial(
    node: BitcoindAdapter | BtclibNodeAdapter,
    connection_type: str,
    services: int,
    *,
    dropped: bool,
) -> None:
    """Have `node` dial the test as `connection_type`, offering `services`.

    Core's own `add_outbound_connection` in this file: where the peer is
    `dropped` it answers the node's `version` with its own and waits for
    the node to close the connection; otherwise it shakes hands, answers
    a `ping` and closes the connection itself. Either way the node's own
    `getpeerinfo` is then awaited empty.
    """
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, connection_type)
        peer = listener.accept()
    with peer:
        if dropped:
            peer.wait_for("version")
            peer.send(Version(services=services, nonce=secrets.randbelow(2**64)))
            peer.wait_for_disconnect()
        else:
            peer.handshake(services=ServiceFlags(services))
            peer.sync_with_ping()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])


def _check_services(
    node: BitcoindAdapter | BtclibNodeAdapter,
    services_tried: Sequence[int],
    desirable: int,
    *,
    dropped: bool,
    log_path: Path | None = None,
) -> None:
    """Core's `test_desirable_service_flags`, over each type expecting services.

    :param log_path: the node's own log where the check is a log half, the
        wording of each refusal then asserted as it is caused.
    """
    for connection_type, services in itertools.product(
        _CONNECTION_TYPES, services_tried
    ):
        if dropped:
            assert services & desirable != desirable
            expected = (
                "does not offer the expected services "
                f"({services:08x} offered, {desirable:08x} expected)"
            )
            with _expecting(log_path, [expected]):
                _dial(node, connection_type, services, dropped=True)
        else:
            assert services & desirable == desirable
            _dial(node, connection_type, services, dropped=False)


def _mine_at(node: BitcoindAdapter | BtclibNodeAdapter, timestamp: int) -> None:
    """Core's `generate_at_mocktime`: one block, the clock at `timestamp`.

    Core's `generate` ends in `sync_all`, whose `sync_mempools` calls
    `syncwithvalidationinterfacequeue`: bitcoind's peer logic learns the
    new tip's time from `UpdatedBlockTip`, an event queued behind the
    block (`src/validationinterface.cpp`), and a dial made before the
    queue drains is judged against the tip before it. The RPC is
    bitcoind's own, so it is called on bitcoind alone.
    """
    node.set_mock_time(timestamp)
    node.mine(1)
    node.set_mock_time(0)
    if isinstance(node, BitcoindAdapter):
        node.rpc.call("syncwithvalidationinterfacequeue")


def outbound_services_decide_the_connection(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: a peer short of the full services is dropped.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    _check_services(
        node,
        (ServiceFlags.NODE_NONE, ServiceFlags.NODE_NETWORK, ServiceFlags.NODE_WITNESS),
        _DESIRABLE_FULL,
        dropped=True,
    )
    _check_services(node, (_DESIRABLE_FULL,), _DESIRABLE_FULL, dropped=False)


def outbound_services_refusal_is_logged(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for each services refusal.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    _check_services(
        node,
        (ServiceFlags.NODE_NONE, ServiceFlags.NODE_NETWORK, ServiceFlags.NODE_WITNESS),
        _DESIRABLE_FULL,
        dropped=True,
        log_path=log_path,
    )


def limited_peer_is_kept_only_near_the_tip(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: a limited peer is dropped a day past the tip alone.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    limited = ServiceFlags.NODE_NETWORK_LIMITED | ServiceFlags.NODE_WITNESS
    _mine_at(node, int(time.time()) - 25 * _ONE_HOUR)
    _check_services(node, (limited,), _DESIRABLE_FULL, dropped=True)
    _mine_at(node, int(time.time()) - 23 * _ONE_HOUR)
    _check_services(node, (limited,), _DESIRABLE_PRUNED, dropped=False)


def limited_peer_refusal_is_logged(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the log half: the limited peer's refusal, the tip a day old.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    limited = ServiceFlags.NODE_NETWORK_LIMITED | ServiceFlags.NODE_WITNESS
    _mine_at(node, int(time.time()) - 25 * _ONE_HOUR)
    _check_services(node, (limited,), _DESIRABLE_FULL, dropped=True, log_path=log_path)


def feeler_is_dropped_after_its_version(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: a feeler is closed once its `version` is read.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    _dial(node, "feeler", ServiceFlags.NODE_NONE, dropped=True)


def feeler_completion_is_logged(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the log half: bitcoind's own wording for the completed feeler.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    with assert_debug_log(log_path, ["feeler connection completed"]):
        _dial(node, "feeler", ServiceFlags.NODE_NONE, dropped=True)


def self_connection_is_dropped(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the wire half: the node drops a connection to its own address.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    node.add_outbound_connection(node.p2p_address, "outbound-full-relay")
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])


def self_connection_is_logged(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check the log half: bitcoind's own wording for the self-connection.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    with assert_debug_log(log_path, ["connected to self", "disconnecting"]):
        node.add_outbound_connection(node.p2p_address, "outbound-full-relay")
        wait_until(lambda: node.rpc.call("getpeerinfo") == [])
