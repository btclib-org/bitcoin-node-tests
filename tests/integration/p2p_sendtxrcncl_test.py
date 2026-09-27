# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_sendtxrcncl`, as bodies over either node.

Read from Core's `test/functional/p2p_sendtxrcncl.py` (`fa4cb96bdec2`,
2026-02-17): BIP330's `sendtxrcncl`, which a node started with
`-txreconciliation` sends ahead of its `verack` to a peer that relays
transactions, and which it registers, ignores or disconnects for when a
peer sends it.

Each group of Core's own steps is a body over a fresh node, run with the
options Core restarts its own with and, where `-txreconciliation` is one
of them, the `-peertimeout` Core's harness gives every node:

- sent to an inbound peer, ahead of the `verack`, and not to one below
  BIP339's protocol version or one asking for no transaction relay, the
  last also with `NODE_BLOOM` offered (`-peerbloomfilters`);
- sent to a full-relay outbound peer and not to a block-relay-only one, a
  feeler or an addr-fetch one, and a block-relay-only peer sending it
  dropped;
- not sent without `-txreconciliation`, nor under `-blocksonly`, and
  ignored without `-txreconciliation`;
- a second `sendtxrcncl` after a valid one, one of version 0 and one
  after `verack`, each dropping the peer;
- one of version 2, one the node did not expect and one from a peer that
  never sent `wtxidrelay`, each kept.

Where Core asserts a log line and the peer's fate is observable on the
wire as well, the step is a wire half and a log half, the log family's
own split (issue #5): a dropped peer is awaited closed, and a kept peer
finishes the handshake and answers a `ping`, which Core's own
`send_and_ping` asserts for the last of them. A log line naming a peer
names it by the id the node's own `getpeerinfo` gives it, where Core's
names the id its sequence of restarts produces.

`Capability.TX_RECONCILIATION` and `Capability.PEER_TIMEOUT` are what
every body but the ones without `-txreconciliation` asks for; those run
with no capability at all, and their log half asks for
`Capability.DEBUG_LOG` alone. Without the `-peertimeout`, a peer that
never sends `verack` is dropped for "version handshake timeout" once
the default bound passes, which a scaled wait for a drop outlasts.

`p2p_sendtxrcncl_bitcoind_test.py` and `p2p_sendtxrcncl_btclib_node_test.py`
run each body, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

import secrets
from contextlib import nullcontext
from typing import TYPE_CHECKING

from btclib.p2p import (
    SendTxRcncl,
    ServiceFlags,
    Verack,
    Version,
    WtxidRelay,
    magic_from_chain,
)
from btclib.p2p.limits import PROTOCOL_VERSION

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Listener, Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "sendtxrcncl_is_ignored_without_the_option",
    "sendtxrcncl_is_ignored_without_the_option_in_the_log",
    "sendtxrcncl_is_not_sent_in_blocks_only_mode",
    "sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay",
    "sendtxrcncl_is_sent_to_full_relay_outbound_peers",
    "sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions",
    "sendtxrcncl_kept_peers_are_logged",
    "sendtxrcncl_kept_peers_stay_connected",
    "sendtxrcncl_on_block_relay_only_is_logged",
    "sendtxrcncl_violations_are_logged",
    "sendtxrcncl_violations_drop_the_peer",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's `P2P_SERVICES` (`test_framework/p2p.py`)
_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS

# BIP339's `WTXID_RELAY_VERSION` less one, Core's own pre-wtxid peer
_PRE_WTXID_VERSION = 70015

# `TXRECONCILIATION_VERSION` (`src/node/txreconciliation.h`)
_TXRECONCILIATION_VERSION = 1

# `-txreconciliation`, beside the `-peertimeout` Core's `write_config` gives
# every node: a peer that never sends `verack` is otherwise dropped for
# "version handshake timeout", a disconnect whatever `sendtxrcncl` did
_OPTIONS = ("-peertimeout=999999999", "-txreconciliation")

# `Peer`'s own default wait, for each message read one at a time
_WAIT = 30.0


def _sendtxrcncl(version: int = _TXRECONCILIATION_VERSION) -> SendTxRcncl:
    """Core's `create_sendtxrcncl_msg`: salt 2, version 1 unless named."""
    return SendTxRcncl(version=version, salt=2)


def _version(*, version: int = PROTOCOL_VERSION, relay: bool | None = None) -> Version:
    """Return the `version` Core's `msg_version` carries, over `_SERVICES`."""
    return Version(
        version=version,
        services=_SERVICES,
        nonce=secrets.randbelow(2**64),
        relay=relay,
    )


def _read_until_verack(peer: Peer) -> list[str]:
    """Return every command read, in order, up to the node's own `verack`."""
    commands: list[str] = []
    while not commands or commands[-1] != "verack":
        commands.append(peer.receive(timeout=scaled(_WAIT)).command)
    return commands


def _connect_inbound(
    node: NodeAdapter,
    *,
    version: int = PROTOCOL_VERSION,
    relay: bool | None = None,
    wtxidrelay: bool = True,
    verack: bool = True,
) -> tuple[Peer, list[str]]:
    """Dial `node` and read up to its `verack`: Core's `add_p2p_connection`.

    The test's `version` goes first, then, once the node's own has
    arrived, BIP339's `wtxidrelay` where Core's `P2PInterface.on_version`
    sends it, and a `verack` unless the peer is Core's `PeerNoVerack`.

    :returns: the peer, and every command it read up to the `verack`.
    """
    peer = Peer(node.p2p_address, magic_from_chain(node.chain))
    try:
        peer.send(_version(version=version, relay=relay))
        peer.wait_for("version")
        if wtxidrelay:
            peer.send(WtxidRelay())
        if verack:
            peer.send(Verack())
        commands = ["version", *_read_until_verack(peer)]
    except BaseException:
        peer.close()
        raise
    return peer, commands


def _dialled(node: NodeAdapter, connection_type: str) -> Peer:
    """Have `node` dial a fresh listener as `connection_type`, and accept."""
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, connection_type)
        return listener.accept()


def _only_peer_id(node: NodeAdapter) -> int:
    """Return the id of the one peer `node` holds."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    (peer,) = peers
    return int(peer["id"])


def _close(node: NodeAdapter, peer: Peer) -> None:
    """Close `peer`, and wait until `node` holds no peer: `disconnect_p2ps`."""
    peer.close()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])


def _received(peer: Peer) -> SendTxRcncl | None:
    """Return the `sendtxrcncl` `peer` read, or `None` where it read none."""
    message = peer.last_message.get("sendtxrcncl")
    return None if message is None else SendTxRcncl.parse(message.payload)


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


def _expecting_of(
    node: NodeAdapter, log_path: Path | None, expected: Callable[[int], str]
) -> AbstractContextManager[None]:
    """Return `_expecting` of the line `expected` words for `node`'s one peer.

    The peer's id is read only for a log half: btclib-node's own
    `getpeerinfo` lists no peer short of its `verack`.
    """
    if log_path is None:
        return nullcontext()
    return assert_debug_log(log_path, [expected(_only_peer_id(node))])


def sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check `sendtxrcncl` reaches an inbound peer that relays, before `verack`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    node.restart(_OPTIONS)

    peer, commands = _connect_inbound(node)
    received = _received(peer)
    assert received is not None
    assert received.version == _TXRECONCILIATION_VERSION
    assert commands.index("sendtxrcncl") < commands.index("verack")
    _close(node, peer)

    peer, _ = _connect_inbound(node, version=_PRE_WTXID_VERSION)
    assert _received(peer) is None
    _close(node, peer)

    peer, _ = _connect_inbound(node, relay=False)
    assert _received(peer) is None
    _close(node, peer)


def sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a peer asking for no relay gets none, `NODE_BLOOM` offered.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    require(Capability.PEER_BLOOM_FILTERS, node.capabilities, skip_counts)
    node.restart([*_OPTIONS, "-peerbloomfilters"])

    peer, _ = _connect_inbound(node, relay=False)
    version = Version.parse(peer.last_message["version"].payload)
    assert version.services & ServiceFlags.NODE_BLOOM
    assert _received(peer) is None
    _close(node, peer)


def sendtxrcncl_is_sent_to_full_relay_outbound_peers(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the outbound types: full relay gets it, the rest do not.

    Then the wire half of a block-relay-only peer sending one: the node
    told it no transaction relay, and drops it.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    node.restart(_OPTIONS)

    for connection_type in ("outbound-full-relay", "block-relay-only", "addr-fetch"):
        peer = _dialled(node, connection_type)
        peer.handshake()
        received = _received(peer)
        if connection_type == "outbound-full-relay":
            assert received is not None
            assert received.version == _TXRECONCILIATION_VERSION
        else:
            assert received is None
        _close(node, peer)

    # Core's `P2PFeelerReceiver`: its own `version` and nothing else
    with _dialled(node, "feeler") as feeler:
        feeler.wait_for("version")
        feeler.send(_version())
        feeler.wait_for_disconnect()
        assert feeler.message_count["sendtxrcncl"] == 0

    _check_block_relay_only_sender(node, None)


def sendtxrcncl_on_block_relay_only_is_logged(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: a block-relay-only peer's `sendtxrcncl` refused.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    node.restart(_OPTIONS)
    _check_block_relay_only_sender(node, log_path)


def _check_block_relay_only_sender(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's last step: `PeerNoVerack` dialled block-relay-only sends one.

    :param log_path: the node's own log where the check is a log half.
    """
    with _dialled(node, "block-relay-only") as peer:
        peer.wait_for("version")
        peer.send(_version())
        peer.send(WtxidRelay())
        peer.wait_for("verack")
        peer_id = _only_peer_id(node)
        expected = (
            "sendtxrcncl received to which we indicated no tx relay, "
            f"disconnecting peer={peer_id}"
        )
        with _expecting(log_path, [expected]):
            peer.send(_sendtxrcncl())
            peer.wait_for_disconnect()


def sendtxrcncl_is_not_sent_in_blocks_only_mode(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check `-blocksonly` withholds `sendtxrcncl` from an inbound peer.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    require(Capability.BLOCKS_ONLY, node.capabilities, skip_counts)
    node.restart([*_OPTIONS, "-blocksonly"])

    peer, commands = _connect_inbound(node)
    assert commands[-1] == "verack"
    assert _received(peer) is None
    _close(node, peer)


def _check_ignored_without_the_option(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's steps without `-txreconciliation`: none sent, one ignored.

    :param log_path: the node's own log where the check is a log half.
    """
    peer, commands = _connect_inbound(node)
    assert commands[-1] == "verack"
    assert _received(peer) is None
    _close(node, peer)

    peer, _ = _connect_inbound(node, verack=False)
    with peer:
        expected = (
            "sendtxrcncl from peer={} ignored, "
            "as our node does not have txreconciliation enabled"
        ).format
        with _expecting_of(node, log_path, expected):
            peer.send(_sendtxrcncl())
            peer.send(Verack())
            peer.sync_with_ping()


def sendtxrcncl_is_ignored_without_the_option(cluster: _Cluster) -> None:
    """Check without `-txreconciliation`: none sent, a peer's own kept.

    Asks for no capability: the option is off, as Core's default has it.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    """
    (node,) = cluster(1)
    _check_ignored_without_the_option(node, None)


def sendtxrcncl_is_ignored_without_the_option_in_the_log(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for the ignored message.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    _check_ignored_without_the_option(node, _debug_log(node, skip_counts))


def _check_violations(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's drops: a second `sendtxrcncl`, version 0, one after `verack`.

    Each peer has read the node's `verack` before it sends, so each drop
    is of a connection the node had accepted.

    :param log_path: the node's own log where the check is a log half.
    """
    peer, _ = _connect_inbound(node, verack=False)
    with peer:
        peer_id = _only_peer_id(node)
        with _expecting(log_path, ["received: sendtxrcncl"]):
            peer.send(_sendtxrcncl())
        expected = (
            "txreconciliation protocol violation (sendtxrcncl received from "
            f"already registered peer), disconnecting peer={peer_id}"
        )
        with _expecting(log_path, [expected]):
            peer.send(_sendtxrcncl())
            peer.wait_for_disconnect()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])

    peer, _ = _connect_inbound(node, verack=False)
    with peer:
        peer_id = _only_peer_id(node)
        expected = f"txreconciliation protocol violation, disconnecting peer={peer_id}"
        with _expecting(log_path, [expected]):
            peer.send(_sendtxrcncl(version=0))
            peer.wait_for_disconnect()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])

    peer, _ = _connect_inbound(node)
    with peer:
        peer.sync_with_ping()
        peer_id = _only_peer_id(node)
        expected = f"sendtxrcncl received after verack, disconnecting peer={peer_id}"
        with _expecting(log_path, [expected]):
            peer.send(_sendtxrcncl())
            peer.wait_for_disconnect()


def sendtxrcncl_violations_drop_the_peer(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: each of Core's violations drops the peer.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    node.restart(_OPTIONS)
    _check_violations(node, None)


def sendtxrcncl_violations_are_logged(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for each violation.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    node.restart(_OPTIONS)
    _check_violations(node, log_path)


def _keep(
    node: NodeAdapter,
    log_path: Path | None,
    expected: Callable[[int], str],
    *,
    sendtxrcncl: SendTxRcncl,
    version: int = PROTOCOL_VERSION,
    wtxidrelay: bool = True,
) -> None:
    """Send `sendtxrcncl` ahead of the `verack`, then answer a `ping`.

    :param expected: the log line the node writes, given the peer's id.
    """
    peer, _ = _connect_inbound(
        node, version=version, wtxidrelay=wtxidrelay, verack=False
    )
    with peer, _expecting_of(node, log_path, expected):
        peer.send(sendtxrcncl)
        peer.send(Verack())
        peer.sync_with_ping()
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])


def _check_kept(node: NodeAdapter, log_path: Path | None) -> None:
    """Core's kept peers: version 2, unexpected, and no `wtxidrelay`.

    :param log_path: the node's own log where the check is a log half.
    """
    _keep(
        node,
        log_path,
        lambda peer_id: f"Register peer={peer_id} (inbound=1)",
        sendtxrcncl=_sendtxrcncl(version=2),
    )
    _keep(
        node,
        log_path,
        lambda peer_id: (
            f"Ignore unexpected txreconciliation signal from peer={peer_id}"
        ),
        sendtxrcncl=_sendtxrcncl(),
        version=_PRE_WTXID_VERSION,
    )
    _keep(
        node,
        log_path,
        lambda peer_id: f"Forget txreconciliation state of peer={peer_id}",
        sendtxrcncl=_sendtxrcncl(),
        wtxidrelay=False,
    )


def sendtxrcncl_kept_peers_stay_connected(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the wire half: each peer Core's log steps keep answers a `ping`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    node.restart(_OPTIONS)
    _check_kept(node, None)


def sendtxrcncl_kept_peers_are_logged(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check the log half: registered, ignored and forgotten, by peer id.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TX_RECONCILIATION, node.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node.capabilities, skip_counts)
    log_path = _debug_log(node, skip_counts)
    node.restart(_OPTIONS)
    _check_kept(node, log_path)
