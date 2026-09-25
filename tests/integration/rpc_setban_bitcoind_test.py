# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, rewritten on this repository's own harness.

Read from Core's `test/functional/rpc_setban.py` (`fa21edddb272`,
2026-03-27): two nodes, `node0` connecting to `node1`; a `setban` on
`node1` matching `node0`'s own address drops the live connection, which
`node.wait_until_disconnected` (`node.py`) waits for -- Core's own
`self.wait_until(lambda: not self.nodes[0].is_connected_to(self.nodes[1]))`
matched by address rather than by `getnetworkinfo`'s own subversion
string, `connect_nodes`'s own docstring has why.

This rewrite drops two of Core's own four sections: the `-whitelist`
noban-permission section and the `-bantime` persistence section each
restart a node with different `extra_args` than it started with (Core's
own `restart_node(1, [...])`), a mechanism `NodeAdapter` does not offer
-- `restart` (`node.py`) reuses the constructor's own `extra_args`
unconditionally -- and no family of this repository has needed yet
([ISS bitcoin-node-tests#51](https://github.com/btclib-org/bitcoin-node-tests/issues/51)).
Kept are the other two of Core's own four: a ban surviving a plain
restart with the same `extra_args` it already had, which `restart`
already does, and reconnection succeeding again once the ban is
removed -- plus the whole of the file's own multi-node subject that
needs no restart at all, a ban dropping a live connection, and the
non-IP address check that needs no second node either. Core's own
reconnection wait after the first restart uses `assert_debug_log`,
naming a peer's own log lines by number; this repository has no
capability that reads a node's own log yet, so the same wait is made
instead through `connect_nodes`' own handshake wait timing out, a
banned dial never completing one.

`Capability.BAN` is bitcoind's alone: `setban`, `listbanned` and
`clearbanned` name no callback in `btclib-node`'s own dispatch table, on
either build measured (`btclib_node.py`'s own docstring;
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088)).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_disconnected

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_ban_drops_the_connection_it_matches(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: `setban` disconnects the peer it matches, live."""
    node0, node1 = bitcoind_cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.BAN, node1.capabilities, skip_counts)

    connect_nodes(node0, node1)
    peers = node1.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert "noban" not in peers[0]["permissions"]

    node1.rpc.call("setban", ["127.0.0.1", "add"])
    wait_until_disconnected(node0, node1)

    banned = node1.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert len(banned) == 1

    node1.rpc.call("clearbanned")
    assert node1.rpc.call("listbanned") == []


def test_a_ban_survives_a_restart_until_it_is_removed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: a plain restart keeps the ban, until unbanned."""
    node0, node1 = bitcoind_cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.BAN, node1.capabilities, skip_counts)

    connect_nodes(node0, node1)
    node1.rpc.call("setban", ["127.0.0.1", "add"])
    wait_until_disconnected(node0, node1)

    node1.restart()
    with pytest.raises(TimeoutError):
        connect_nodes(node0, node1, timeout=2.0)

    node1.rpc.call("setban", ["127.0.0.1", "remove"])
    node1.restart()
    connect_nodes(node0, node1)
    peers = node1.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert "noban" not in peers[0]["permissions"]


def test_a_non_ip_address_can_be_banned_and_unbanned(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: an onion address bans and unbans the same way."""
    (node,) = bitcoind_cluster(1)
    require(Capability.BAN, node.capabilities, skip_counts)
    tor_address = "pg6mmjiyjmcrsslvykfwnntlaru7p5svn6y2ymmju6nubxndf4pscryd.onion"

    node.rpc.call("setban", [tor_address, "add"])
    banned = node.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert any(entry["address"] == tor_address for entry in banned)

    node.rpc.call("setban", [tor_address, "remove"])
    assert node.rpc.call("listbanned") == []
