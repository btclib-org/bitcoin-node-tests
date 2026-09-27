# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_add_connections`, as bodies over either node.

Read from Core's `test/functional/p2p_add_connections.py`
(`4c79f3a34d00`, 2026-09-14): a node made to dial listening test peers by
connection type, its counts read back from `getnetworkinfo`, the peers
dropped and dialled again, then again after a restart; a feeler the node
drops once it has read the test's `version`, and a peer that sends its
own `version` before reading the node's.

Core's first step, a `manual` connection past a filled outbound
capacity, is a body of its own over a fresh node, and is read per-build
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)):
`addconnection` takes `manual` only past the pinned `v31.1`
(bitcoin/bitcoin@4c79f3a34d003bd97824b032383ac816a4147d68). Where the
build's own `help addconnection` names no `manual`, the body asserts the
refusal Core's `RPC_INVALID_PARAMETER` answers instead. Core starts that
node with `-listen=0`, which this adapter's own `-bind` refuses at
startup, so it listens here: `-maxconnections=1` leaves room for one
full-relay connection either way, `addconnection` refusing a second as
over capacity.

What else differs from Core's own file:

- every dialled peer listens on a port of its own, as Core's `p2p_idx`
  gives it one: the node drops a dial to a destination it already holds
  a connection to;
- `disconnect_p2ps` is every test peer closed and the node's own
  `getpeerinfo` awaited empty, the node having no peer of any other kind;
- the restart closes node 0's test peers first, where Core's own
  `stop_node` forgets them.

`p2p_add_connections_bitcoind_test.py` and
`p2p_add_connections_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.p2p import ServiceFlags, Verack, Version, WtxidRelay, magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Listener, Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "manual_connection_past_the_outbound_capacity",
    "outbound_connections_by_type",
]

# Core's `RPCErrorCode::RPC_INVALID_PARAMETER` (`src/rpc/protocol.h`),
# what `addconnection` throws for a connection type it does not name
_RPC_INVALID_PARAMETER = -8

# Core's `P2P_SERVICES` (`test_framework/p2p.py`), what its
# `P2PInterface` offers unless a test names others
_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS


def _add_outbound(node: NodeAdapter, connection_type: str) -> Peer:
    """Have `node` dial a fresh listener as `connection_type`, and shake hands.

    Core's `add_outbound_p2p_connection`, whose own wait ends on the
    `verack` and a `sync_with_ping`.
    """
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, connection_type)
        peer = listener.accept()
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _add_inbound(node: NodeAdapter) -> Peer:
    """Dial `node`, and shake hands: Core's `add_p2p_connection`."""
    peer = Peer(node.p2p_address, magic_from_chain(node.chain))
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _check_node_connections(node: NodeAdapter, num_in: int, num_out: int) -> None:
    """Core's `check_node_connections`: `getnetworkinfo`'s in and out counts."""
    info = node.rpc.call("getnetworkinfo")
    assert isinstance(info, dict)
    assert info["connections_in"] == num_in
    assert info["connections_out"] == num_out


def _disconnect_p2ps(node: NodeAdapter, peers: list[Peer]) -> None:
    """Close every test peer of `node`, and wait until the node has none."""
    for peer in peers:
        peer.close()
    peers.clear()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])


def _version() -> Version:
    """Return the `version` Core's `P2PInterface.send_version` would send."""
    return Version(services=_SERVICES, nonce=secrets.randbelow(2**64))


def _takes_manual(node: NodeAdapter) -> bool:
    """Return whether this build's own `addconnection` names `manual`.

    The per-build fact ISS 35 reads rather than assumes: the connection
    types are listed in the RPC's own help, `"manual"` among them on a
    build carrying bitcoin/bitcoin@4c79f3a34d00 and absent before it.
    """
    help_text = node.rpc.call("help", ["addconnection"])
    assert isinstance(help_text, str)
    return '"manual"' in help_text


def manual_connection_past_the_outbound_capacity(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a `manual` connection past one that fills the outbound capacity.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    node.restart(["-maxconnections=1"])
    peers = [_add_outbound(node, "outbound-full-relay")]
    try:
        if _takes_manual(node):
            peers.append(_add_outbound(node, "manual"))
            expected = {"manual", "outbound-full-relay"}
        else:
            with (
                Listener(magic_from_chain(node.chain)) as listener,
                pytest.raises(RpcError) as refusal,
            ):
                node.add_outbound_connection(listener.address, "manual")
            assert refusal.value.code == _RPC_INVALID_PARAMETER
            expected = {"outbound-full-relay"}
        peer_info = node.rpc.call("getpeerinfo")
        assert isinstance(peer_info, list)
        assert {peer["connection_type"] for peer in peer_info} == expected
        _disconnect_p2ps(node, peers)
    finally:
        for peer in peers:
            peer.close()


def outbound_connections_by_type(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check typed outbound counts, a feeler and an early `version`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.TYPED_OUTBOUND, node0.capabilities, skip_counts)
    peers0: list[Peer] = []
    peers1: list[Peer] = []
    try:
        peers0 += [_add_outbound(node0, "outbound-full-relay") for _ in range(8)]
        peers0 += [_add_outbound(node0, "block-relay-only") for _ in range(2)]
        peers1 += [_add_outbound(node1, "block-relay-only") for _ in range(2)]
        peers1 += [_add_inbound(node1) for _ in range(5)]
        peers1 += [_add_outbound(node1, "outbound-full-relay") for _ in range(8)]

        _check_node_connections(node0, 0, 10)
        _check_node_connections(node1, 5, 10)

        _disconnect_p2ps(node0, peers0)
        _check_node_connections(node0, 0, 0)

        peers0 += [_add_outbound(node0, "outbound-full-relay") for _ in range(8)]
        _check_node_connections(node0, 0, 8)
        peers0 += [_add_outbound(node0, "block-relay-only") for _ in range(2)]
        _check_node_connections(node0, 0, 10)

        for peer in peers0:
            peer.close()
        peers0.clear()
        node0.restart()

        peers0 += [_add_outbound(node0, "outbound-full-relay") for _ in range(4)]
        _check_node_connections(node0, 0, 4)
        peers0 += [_add_outbound(node0, "block-relay-only") for _ in range(2)]
        _check_node_connections(node0, 0, 6)

        _check_node_connections(node1, 5, 10)

        _feeler_is_dropped_after_its_version(node0)
        peers0.append(_version_sent_early_is_tolerated(node0))
    finally:
        for peer in peers0 + peers1:
            peer.close()


def _feeler_is_dropped_after_its_version(node: NodeAdapter) -> None:
    """Core's `P2PFeelerReceiver`: answer the `version`, then be dropped.

    The node closes a feeler once it has processed the test's `version`,
    so the test sends nothing after it: the node's own `version` is the
    one it counts, and that `version` asks for no transaction relay.
    """
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, "feeler")
        feeler = listener.accept()
    with feeler:
        feeler.wait_for("version")
        feeler.send(_version())
        feeler.wait_for_disconnect()
        assert feeler.message_count["version"] == 1
        version = Version.parse(feeler.last_message["version"].payload)
        assert version.relay is False


def _version_sent_early_is_tolerated(node: NodeAdapter) -> Peer:
    """Core's `VersionSender`: send the `version` before reading the node's.

    The node's own `version` goes out before it processes the test's, so
    the handshake completes and a `ping` is answered.
    """
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, "outbound-full-relay")
        peer = listener.accept()
    peer.send(_version())
    peer.wait_for("version")
    peer.send(WtxidRelay())
    peer.send(Verack())
    peer.wait_for("verack")
    peer.sync_with_ping()
    return peer
