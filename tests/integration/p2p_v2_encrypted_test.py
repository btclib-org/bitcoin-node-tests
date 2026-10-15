# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_v2_encrypted`, as bodies over either node.

Read from Core's `test/functional/p2p_v2_encrypted.py` (`fab352053d6e`,
2026-04-16): a node started with `-v2transport=1` takes test peers
speaking v2 and v1, inbound and outbound, each read back from
`getpeerinfo`'s `transport_protocol_type`; blocks then reach it over a v2
peer past `REKEY_INTERVAL` packets, sent first as decoys it ignores and
then as messages it takes, and reach a second node over a v2 connection
between the two. Restarted with `-v2transport=0`, the node takes a v1
peer.

What differs from Core's file:

- Core's run is split into two bodies: the inbound connections with
  the blocks and the restart, and the outbound connections, which need
  `addconnection` (`Capability.TYPED_OUTBOUND`). Each body checks the
  `version` sent and the `verack` received of its own peers, and the
  connection counts of its own half;
- the peer answers the node's `getdata` while it waits for the last
  block to be asked for, where Core's `P2PDataStore` answers from its
  network thread;
- the test peers are closed before the restart, where Core's own
  `restart_node` forgets them.

`p2p_v2_encrypted_bitcoind_test.py` and
`p2p_v2_encrypted_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import magic_from_chain
from btclib.block.block import Block
from btclib.block.build import build_coinbase
from btclib.block.mining import candidate_block_header, mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import BlockPayload, GetData, Headers, Ping, Pong, ServiceFlags
from btclib.p2p.bip324 import REKEY_INTERVAL

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import (
    connect_nodes,
    disconnect_nodes,
    sync_all,
    wait_until,
)
from bitcoin_node_tests.peer import Listener, Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["inbound_connections_and_blocks", "outbound_connections"]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# Core's `P2P_SERVICES` (`test_framework/p2p.py`), and what its
# `TestNode` adds to them for a node started with `-v2transport=1`
_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS
_V2_SERVICES = _SERVICES | ServiceFlags.NODE_P2P_V2

# `OP_TRUE`, what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"

# Core's own default wait, `send_blocks_and_test`'s
_WAIT = 60.0


def _pair(
    cluster: _Cluster, skip_counts: SkipCounts
) -> tuple[NodeAdapter, NodeAdapter]:
    """Return two nodes started with `-v2transport=1`, Core's `extra_args`.

    The first node's own capabilities are asked before the second one
    starts, so a node not declaring them is skipped on one start.
    """
    (node0,) = cluster(1)
    for capability in (
        Capability.V2TRANSPORT,
        Capability.CONNECT,
        Capability.DISCONNECT,
    ):
        require(capability, node0.capabilities, skip_counts)
    node0, node1 = cluster(1)
    node0.restart(["-v2transport=1"])
    node1.restart(["-v2transport=1"])
    return node0, node1


def _add_p2p_connection(
    node: NodeAdapter, peers: list[Peer], *, supports_v2_p2p: bool, node_v2: bool
) -> Peer:
    """Core's `TestNode.add_p2p_connection(P2PInterface(), ...)`.

    The peer speaks v2 only where the node was started with
    `-v2transport=1` (`node_v2`), as Core's `TestNode` decides.
    """
    peer = Peer(node.p2p_address, _MAGIC, supports_v2_p2p=supports_v2_p2p and node_v2)
    peers.append(peer)
    peer.handshake(services=_V2_SERVICES if node_v2 else _SERVICES)
    peer.sync_with_ping()
    return peer


def _add_outbound_p2p_connection(
    node: NodeAdapter,
    peers: list[Peer],
    *,
    supports_v2_p2p: bool,
    advertise_v2_p2p: bool,
) -> Peer:
    """Core's `TestNode.add_outbound_p2p_connection(P2PInterface(), ...)`.

    `addconnection`'s own `v2transport` is `advertise_v2_p2p`. Where the
    node is told the peer speaks v2 and it does not, the node's v2 key
    reaches a v1 peer, which closes the connection on it, and the node
    dials again over v1.
    """
    with Listener(_MAGIC) as listener:
        host, port = listener.address
        node.rpc.call(
            "addconnection", [f"{host}:{port}", "outbound-full-relay", advertise_v2_p2p]
        )
        if advertise_v2_p2p and not supports_v2_p2p:
            with listener.accept() as refused, pytest.raises(ValueError, match="magic"):
                refused.receive()
        peer = listener.accept(supports_v2_p2p=supports_v2_p2p and advertise_v2_p2p)
    peers.append(peer)
    peer.handshake(services=_V2_SERVICES if advertise_v2_p2p else _SERVICES)
    peer.sync_with_ping()
    return peer


def _peer_info(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `getpeerinfo`, checked to be a list of objects."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert all(isinstance(peer, dict) for peer in peers)
    return peers


def _last_transport(node: NodeAdapter) -> object:
    """Core's `getpeerinfo()[-1]["transport_protocol_type"]`."""
    return _peer_info(node)[-1]["transport_protocol_type"]


def _check_version_and_verack(node: NodeAdapter, count: int) -> None:
    """Check `count` peers: each sent a `version`, each sent back a `verack`."""
    peers = _peer_info(node)
    assert len(peers) == count
    for peer in peers:
        sent = peer["bytessent_per_msg"]
        received = peer["bytesrecv_per_msg"]
        assert isinstance(sent, dict)
        assert isinstance(received, dict)
        assert sent["version"] > 0
        assert received["verack"] > 0


def _check_node_connections(node: NodeAdapter, num_in: int, num_out: int) -> None:
    """Core's `check_node_connections`: `getnetworkinfo`'s in and out counts."""
    info = node.rpc.call("getnetworkinfo")
    assert isinstance(info, dict)
    assert info["connections_in"] == num_in
    assert info["connections_out"] == num_out


def _generate_blocks(node: NodeAdapter, number: int) -> list[Block]:
    """Core's own `generate_blocks`: `number` blocks on `node`'s tip, not sent.

    Each is Core's `create_block`, its coinbase paying `OP_TRUE`, a
    second after the block before it.
    """
    tip_hash = node.rpc.call("getbestblockhash")
    assert isinstance(tip_hash, str)
    tip = node.rpc.call("getblock", [tip_hash])
    assert isinstance(tip, dict)
    previous = bytes.fromhex(tip_hash)
    height = tip["height"]
    block_time = tip["time"]
    blocks = []
    for _ in range(number):
        height += 1
        block_time += 1
        coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
        header = candidate_block_header(
            previous,
            [coinbase],
            datetime.fromtimestamp(block_time, UTC),
            REGTEST_POW_LIMIT_BITS,
        )
        solved = mine(header)
        assert solved is not None
        block = Block(solved, [coinbase], check_validity=False)
        blocks.append(block)
        previous = block.header.hash
    return blocks


def _block_payload(block: Block) -> BlockPayload:
    """Core's own `msg_block(block)`."""
    return BlockPayload(block, include_witness=True, check_validity=False)


def _serve_until_asked(peer: Peer, blocks: Sequence[Block]) -> None:
    """Answer the node's `getdata` from `blocks` until it asks for the last.

    Core's `P2PDataStore.on_getdata`, and its `send_blocks_and_test`'s
    wait for the last block's `getdata`; a `ping` is answered meanwhile.

    :raises TimeoutError: the last block was not asked for within the wait.
    """
    store = {block.header.hash: block for block in blocks}
    last = blocks[-1].header.hash
    deadline = time.monotonic() + scaled(_WAIT)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            err_msg = "the last block was never asked for within the wait"
            raise TimeoutError(err_msg)
        message = peer.receive(timeout=remaining)
        if message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))
        if message.command != "getdata":
            continue
        items = GetData.parse(message.payload, check_validity=False).items
        for item in items:
            if item.hash in store:
                peer.send(_block_payload(store[item.hash]), check_validity=False)
        if any(item.hash == last for item in items):
            return


def _send_blocks_and_test(
    peer: Peer, node: NodeAdapter, blocks: Sequence[Block], *, is_decoy: bool
) -> None:
    """Core's `P2PDataStore.send_blocks_and_test(blocks, node, ...)`.

    As decoys, the blocks are sent unasked and the node's tip does not
    move; otherwise their headers go first, the blocks are sent as the
    node asks for them, and its tip becomes the last.
    """
    last = blocks[-1].header.hash.hex()
    if is_decoy:
        for block in blocks:
            peer.send(_block_payload(block), check_validity=False, is_decoy=True)
    else:
        peer.send(Headers([block.header for block in blocks], check_validity=False))
        _serve_until_asked(peer, blocks)
    peer.sync_with_ping(timeout=_WAIT)
    if is_decoy:
        assert node.rpc.call("getbestblockhash") != last
    else:
        wait_until(lambda: node.rpc.call("getbestblockhash") == last, timeout=_WAIT)


def inbound_connections_and_blocks(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check inbound v2 and v1 peers, blocks past a rekeying, and a v1 restart.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = _pair(cluster, skip_counts)
    peers: list[Peer] = []
    try:
        peer1 = _add_p2p_connection(node0, peers, supports_v2_p2p=True, node_v2=True)
        assert peer1.supports_v2_p2p
        assert _last_transport(node0) == "v2"

        peer2 = _add_p2p_connection(node0, peers, supports_v2_p2p=False, node_v2=True)
        assert not peer2.supports_v2_p2p
        assert _last_transport(node0) == "v1"

        _check_version_and_verack(node0, 2)

        # more blocks than packets between two rekeyings
        test_blocks = _generate_blocks(node0, REKEY_INTERVAL + 1)
        for is_decoy in (True, False):
            peer6 = _add_p2p_connection(
                node0, peers, supports_v2_p2p=True, node_v2=True
            )
            assert peer6.supports_v2_p2p
            assert _last_transport(node0) == "v2"
            _send_blocks_and_test(peer6, node0, test_blocks, is_decoy=is_decoy)

            connect_nodes(node0, node1, v2transport=True)
            sync_all([node0, node1])
            assert node0.rpc.call("getbestblockhash") == node1.rpc.call(
                "getbestblockhash"
            )
            disconnect_nodes(node0, node1)

        _check_node_connections(node0, 4, 0)

        for peer in peers:
            peer.close()
        peers.clear()
        node0.restart(["-v2transport=0"])
        peer1 = _add_p2p_connection(node0, peers, supports_v2_p2p=True, node_v2=False)
        assert not peer1.supports_v2_p2p
        assert _last_transport(node0) == "v1"
        _check_node_connections(node0, 1, 0)
    finally:
        for peer in peers:
            peer.close()


def outbound_connections(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check outbound peers: v1, v1 advertised as v2, and v2.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.V2TRANSPORT, node.capabilities, skip_counts)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    node.restart(["-v2transport=1"])
    peers: list[Peer] = []
    try:
        peer3 = _add_outbound_p2p_connection(
            node, peers, supports_v2_p2p=False, advertise_v2_p2p=False
        )
        assert not peer3.supports_v2_p2p
        assert _last_transport(node) == "v1"

        # the node downgrades here
        peer4 = _add_outbound_p2p_connection(
            node, peers, supports_v2_p2p=False, advertise_v2_p2p=True
        )
        assert not peer4.supports_v2_p2p
        assert _last_transport(node) == "v1"

        peer5 = _add_outbound_p2p_connection(
            node, peers, supports_v2_p2p=True, advertise_v2_p2p=True
        )
        assert peer5.supports_v2_p2p
        assert _last_transport(node) == "v2"

        _check_version_and_verack(node, 3)
        _check_node_connections(node, 0, 3)
    finally:
        for peer in peers:
            peer.close()
