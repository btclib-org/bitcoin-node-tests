# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_disconnect_ban`, its `disconnectnode` half, over either node.

Read from Core's `test/functional/p2p_disconnect_ban.py` (`dcd90fbe54cf`,
2026-04-07), the section its own log names "Test disconnectnode RPCs":
two nodes connected both ways, `disconnectnode` refusing an address and
a node id given together and an address no peer has, then dropping a
peer by address, the pair reconnecting, and a peer dropped by node id.
The file's `setban` half is not here: it sets a mock clock, reads
`debug.log` and deletes `banlist.json` from the data directory, `TF2.md`'s
node-linking section has where it went.

Core takes `node0`'s first `getpeerinfo` entry for the address it drops
and expects back after the reconnection. That entry is `node0`'s own
outbound connection to `node1`, the first of the two made, and this
picks it by address instead: an inbound entry's address is an
ephemeral port no reconnection returns to. The node id Core drops next
is the first entry again, whichever it is, and so is it here -- either
connection dropped leaves `node1` one peer.

`p2p_disconnect_ban_bitcoind_test.py` and
`p2p_disconnect_ban_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["disconnectnode_drops_a_peer_by_address_and_by_node_id"]


def _peers(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `node`'s own `getpeerinfo` answer, checked to be a list."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    return peers


def disconnectnode_drops_a_peer_by_address_and_by_node_id(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: `disconnectnode`'s refusals and both its forms.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.DISCONNECT, node0.capabilities, skip_counts)

    connect_nodes(node0, node1)
    connect_nodes(node1, node0)
    host, port = node1.p2p_address
    address1 = f"{host}:{port}"

    peer = _peers(node0)[0]
    with pytest.raises(
        RpcError, match=r"Only one of address and nodeid should be provided\."
    ) as excinfo:
        node0.rpc.call(
            "disconnectnode", {"address": peer["addr"], "nodeid": peer["id"]}
        )
    assert excinfo.value.code == -32602

    with pytest.raises(RpcError, match="Node not found in connected nodes") as excinfo:
        node0.rpc.call("disconnectnode", {"address": "221B Baker Street"})
    assert excinfo.value.code == -29

    assert address1 in [peer["addr"] for peer in _peers(node0)]
    node0.rpc.call("disconnectnode", {"address": address1})
    wait_until(lambda: len(_peers(node1)) == 1)
    assert address1 not in [peer["addr"] for peer in _peers(node0)]

    connect_nodes(node0, node1)
    peers = _peers(node0)
    assert len(peers) == 2
    assert address1 in [peer["addr"] for peer in peers]

    id1 = peers[0]["id"]
    node0.rpc.call("disconnectnode", {"nodeid": id1})
    wait_until(lambda: len(_peers(node1)) == 1)
    assert id1 not in [peer["id"] for peer in _peers(node0)]
