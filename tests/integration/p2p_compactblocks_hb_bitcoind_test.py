# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks_hb`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_compactblocks_hb.py` (`fa5f29774872`,
2025-12-16): six nodes, node 0 the block producer, node 1 the node under
test with an outbound peer (node 2) and three inbound ones (nodes 3-5),
and the subject is which of node 1's peers gets reserved the
high-bandwidth compact-block slot as blocks are relayed through each in
turn -- BIP152's own selection policy, read off `getpeerinfo`'s
`bip152_hb_to`/`bip152_hb_from` rather than off a log line.

Core identifies a peer on node 1 by its `subver`, each `TestNode`
started with `-uacomment=testnode<i>`; this rewrite starts every node
identically and identifies a peer by *when* it connected instead --
node 1's own four peers connect once, in the fixed order 3, 4, 5, 2, and
never again, so recording the new entry `getpeerinfo` gains right after
each `connect_nodes` call is the same identity Core's `subver` match
gives, without a command-line flag this adapter does not carry.

`Capability.MINE` (node 0 mines) and `Capability.CONNECT` (the six-node
topology, and `disconnectnode` alongside `addnode`) are bitcoind's
unconditionally, so this is Core's own claim in full.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import (
    connect_nodes,
    disconnect_nodes,
    wait_until,
    wait_until_tips_agree,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# node 1's own peers, in the topology Core's docstring draws: an outbound
# connection to node 2, inbound ones from nodes 3, 4 and 5
_NODE1_PEERS = (2, 3, 4, 5)


def _connect_and_track_on_node1(
    node1: BitcoindAdapter,
    other: BitcoindAdapter,
    peer_ids: dict[int, int],
    key: int,
    *,
    node1_dials: bool,
    timeout: float = 30.0,
) -> None:
    """Connect `node1` and `other`, and record the peer id `node1` gains.

    `node1`'s own `getpeerinfo` is read before and after: every
    connection this test makes to it happens once and never twice for
    the same peer, so the entry that appears is the one this call just
    made, whichever side dialled -- `node1_dials` is only the direction
    `connect_nodes` needs, node 1's own outbound peer (2) and its inbound
    ones (3, 4, 5) being dialled the opposite way.
    """
    before = {peer["id"] for peer in node1.rpc.call("getpeerinfo")}
    if node1_dials:
        connect_nodes(node1, other)
    else:
        connect_nodes(other, node1)

    def _new_peer_appeared() -> bool:
        after = {peer["id"] for peer in node1.rpc.call("getpeerinfo")}
        new_ids = after - before
        if new_ids:
            peer_ids[key] = new_ids.pop()
            return True
        return False

    wait_until(_new_peer_appeared, timeout=timeout)


def _hb_to(node1: BitcoindAdapter, peer_id: int) -> bool:
    """Return whether node 1 selected the peer named by `peer_id` as HB."""
    for peer in node1.rpc.call("getpeerinfo"):
        if peer["id"] == peer_id:
            return bool(peer["bip152_hb_to"])
    err_msg = f"node 1 no longer reports peer {peer_id}"
    raise AssertionError(err_msg)


def _hb_from(node: BitcoindAdapter) -> bool:
    """Return whether this node's own (and only) peer selected it as HB."""
    peers = node.rpc.call("getpeerinfo")
    return bool(peers[0]["bip152_hb_from"])


def test_reserved_high_bandwidth_slot_for_the_outbound_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: the outbound peer keeps its HB slot on reconnect."""
    node0, node1, node2, node3, node4, node5 = bitcoind_cluster(6)
    nodes = {1: node1, 2: node2, 3: node3, 4: node4, 5: node5}
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)

    # connect everyone to node 0, and mine to get out of IBD; Core's own
    # self.generate() waits for every connected node to reach the new tip
    # before returning, and disconnecting early here would let nodes 1-5
    # cross-relay a backlog to each other once the tracking phase below
    # connects them, granting HB status ahead of the sequence under test
    for i in (1, 2, 3, 4, 5):
        connect_nodes(nodes[i], node0)
    node0.mine(2)
    wait_until_tips_agree([node0, *nodes.values()])
    for i in (1, 2, 3, 4, 5):
        disconnect_nodes(nodes[i], node0)

    # node 1: an outbound peer (2), inbound ones from 3, 4 and 5
    peer_ids: dict[int, int] = {}
    _connect_and_track_on_node1(node1, node3, peer_ids, 3, node1_dials=False)
    _connect_and_track_on_node1(node1, node4, peer_ids, 4, node1_dials=False)
    _connect_and_track_on_node1(node1, node5, peer_ids, 5, node1_dials=False)
    _connect_and_track_on_node1(node1, node2, peer_ids, 2, node1_dials=True)

    def status_to() -> list[bool]:
        return [_hb_to(node1, peer_ids[i]) for i in _NODE1_PEERS]

    def status_from() -> list[bool]:
        return [_hb_from(nodes[i]) for i in _NODE1_PEERS]

    def relay_block_through(i: int) -> list[bool]:
        # Core's own `self.generate` waits for every node to reach the new
        # tip before its caller disconnects anything; the whole mesh is one
        # connected component through node 1's own links to 2, 4 and 5, so
        # that wait is what this mirrors -- disconnecting `i` from node 0
        # first would race the block's own arrival over that one link it
        # is about to sever.
        connect_nodes(nodes[i], node0)
        node0.mine(1)
        wait_until_tips_agree([node0, *nodes.values()])
        disconnect_nodes(nodes[i], node0)
        wait_until(lambda: status_to() == status_from())
        return status_to()

    for i in (3, 4, 5):
        status = relay_block_through(i)
        assert status == [False, i >= 3, i >= 4, i >= 5]

    # relaying again through the same three does not change HB status
    for i in (3, 4, 5):
        status = relay_block_through(i)
        assert status == [False, True, True, True]

    # relaying through the outbound peer (2) takes HB status from an inbound
    status = relay_block_through(2)
    assert status[0] is True
    assert sum(status) == 3

    # 2 stays outbound, so it keeps its slot through 3, 4 and 5 again
    for i in (3, 4, 5):
        status = relay_block_through(i)
        assert status[0]
        assert status[_NODE1_PEERS.index(i)]
        assert sum(status) == 3

    # reconnecting the outbound peer hands the three inbounds HB status again
    disconnect_nodes(node1, node2)
    _connect_and_track_on_node1(node1, node2, peer_ids, 2, node1_dials=True)
    for i in (3, 4, 5):
        status = relay_block_through(i)
        assert not status[0]
        assert status[_NODE1_PEERS.index(i)]
    assert status == [False, True, True, True]
