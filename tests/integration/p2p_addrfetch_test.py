# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addrfetch`, one body over either node.

Read from Core's `test/functional/p2p_addrfetch.py` (`3fd68a95e68b`,
2026-04-07): the node dials an addr-fetch peer the test listens as, sends
it a `getaddr` and no `getheaders`, keeps it through a one-address
`addr`, drops it on a longer one, and drops one that sends nothing once
the clock passes five minutes. Core runs both peers on one node; here
each half is a body of its own, over a fresh node, so the second peer's
node id is `0` where Core's is `1`. `p2p_addrfetch_bitcoind_test.py` and
`p2p_addrfetch_btclib_node_test.py` run them,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from btclib.p2p import (
    Addr,
    NetworkAddress,
    ServiceFlags,
    TimestampedNetworkAddress,
    magic_from_chain,
)

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Listener

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from bitcoin_node_tests.peer import Peer

__all__ = [
    "addr_fetch_peer_is_asked_for_addresses_and_dropped_on_many",
    "addr_fetch_peer_sending_nothing_is_dropped_after_five_minutes",
]

_ADDR = TimestampedNetworkAddress(
    int(time.time()),
    NetworkAddress(
        ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS, "192.0.0.8", 18444
    ),
)


def _add_addr_fetch_peer(node: NodeAdapter, listener: Listener) -> Peer:
    """Have `node` dial `listener` as addr-fetch, and complete the handshake."""
    node.add_outbound_connection(listener.address, "addr-fetch")
    peer = listener.accept()
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _assert_addr_fetch_peers(node: NodeAdapter, peer_ids: list[int]) -> None:
    """Core's `assert_getpeerinfo`: exactly these ids, each one addr-fetch."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert [peer["id"] for peer in peers] == peer_ids
    assert all(peer["connection_type"] == "addr-fetch" for peer in peers)


def addr_fetch_peer_is_asked_for_addresses_and_dropped_on_many(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check the `getaddr`, no `getheaders`, one address kept, two dropped.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    with Listener(magic_from_chain(node.chain)) as listener:
        peer = _add_addr_fetch_peer(node, listener)
    try:
        _assert_addr_fetch_peers(node, [0])

        peer.sync_with_ping()
        assert peer.message_count["getaddr"] == 1
        assert peer.message_count["getheaders"] == 0

        peer.send(Addr([_ADDR]))
        peer.sync_with_ping()
        _assert_addr_fetch_peers(node, [0])

        peer.send(Addr([_ADDR, _ADDR]))
        peer.wait_for_disconnect()
    finally:
        peer.close()


def addr_fetch_peer_sending_nothing_is_dropped_after_five_minutes(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check the peer is kept at 295 s on the node's clock, dropped at 301 s.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    with Listener(magic_from_chain(node.chain)) as listener:
        peer = _add_addr_fetch_peer(node, listener)
    try:
        time_now = int(time.time())
        _assert_addr_fetch_peers(node, [0])

        node.set_mock_time(time_now + 295)
        _assert_addr_fetch_peers(node, [0])

        node.set_mock_time(time_now + 301)
        peer.wait_for_disconnect()
        _assert_addr_fetch_peers(node, [])
    finally:
        peer.close()
