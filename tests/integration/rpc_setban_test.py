# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, one body per test over either node.

Read from Core's `test/functional/rpc_setban.py` (`fa21edddb272`,
2026-03-27): two nodes, `node0` connecting to `node1`; a `setban` on
`node1` matching `node0`'s own address drops the live connection, which
`node.wait_until_disconnected` (`node.py`) waits for -- Core's own
`self.wait_until(lambda: not self.nodes[0].is_connected_to(self.nodes[1]))`
matched by address rather than by `getnetworkinfo`'s own subversion
string, `connect_nodes`'s own docstring has why.

Core's own `-whitelist=127.0.0.1` section, granting a banned peer the
noban permission, and its `-bantime=1234` section, setting the duration
a new ban is given, restart a node with `extra_args` it did not start
with: `restart([...])` (`node.py`) uses them for that start alone,
matching Core's own `restart_node(1, [...])`. Where Core restarts with
`[]`, the node's own start argv, `restart()` is the same restart.

The plain restart's own ban check reads `listbanned` first, the way
Core's own `is_banned` helper does, before the refused reconnection is
even attempted: a `TimeoutError` out of `connect_nodes` is otherwise no
different from a slow start, a port problem or a handshake stall, none
of them the ban this test names
([ISS 94](https://github.com/btclib-org/bitcoin-node-tests/issues/94)).
The dial itself is then read the way Core's own reconnection wait is,
over `assert_debug_log` (`debug_log.py`) rather than the timeout alone:
bitcoind's own `CreateNodeFromAcceptedSocket` (`src/net.cpp`) logs
`dropped (banned)` the moment it refuses the accepted socket, which
`Capability.DEBUG_LOG` gates.

`BitcoindAdapter` declares `Capability.BAN` for every build, and
`BtclibNodeAdapter` only for a build whose dispatch table names `setban`,
`listbanned` and `clearbanned` (`btclib_node.py`'s own docstring).
`rpc_setban_bitcoind_test.py` and `rpc_setban_btclib_node_test.py` run
each body, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import connect_nodes, wait_until_disconnected

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "a_ban_drops_the_connection_it_matches",
    "a_ban_survives_a_restart_until_it_is_removed",
    "a_noban_permission_reconnects_a_banned_peer",
    "a_non_ip_address_can_be_banned_and_unbanned",
    "bantime_given_at_a_restart_sets_a_new_ban_s_duration",
]


def a_ban_drops_the_connection_it_matches(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: `setban` disconnects the peer it matches, live.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
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


def a_ban_survives_a_restart_until_it_is_removed(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: a plain restart keeps the ban, until unbanned.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.BAN, node1.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, node1.capabilities, skip_counts)

    connect_nodes(node0, node1)
    node1.rpc.call("setban", ["127.0.0.1", "add"])
    wait_until_disconnected(node0, node1)

    node1.restart()
    banned = node1.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert [entry["address"] for entry in banned] == ["127.0.0.1/32"]

    if not isinstance(node1, BitcoindAdapter):
        err_msg = f"{type(node1).__name__} declares DEBUG_LOG with no debug_log_path"
        raise TypeError(err_msg)
    with (
        assert_debug_log(node1.debug_log_path, ["dropped (banned)"]),
        pytest.raises(TimeoutError),
    ):
        connect_nodes(node0, node1, timeout=2.0)

    node1.rpc.call("setban", ["127.0.0.1", "remove"])
    node1.restart()
    connect_nodes(node0, node1)
    peers = node1.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert "noban" not in peers[0]["permissions"]


def a_noban_permission_reconnects_a_banned_peer(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: `-whitelist` given at a restart overrides the ban.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.BAN, node1.capabilities, skip_counts)

    node1.rpc.call("setban", ["127.0.0.1", "add"])
    node1.restart(["-whitelist=127.0.0.1"])
    connect_nodes(node0, node1)
    peers = node1.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    assert "noban" in peers[0]["permissions"]
    banned = node1.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert [entry["address"] for entry in banned] == ["127.0.0.1/32"]


def a_non_ip_address_can_be_banned_and_unbanned(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: an onion address bans and unbans the same way.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.BAN, node.capabilities, skip_counts)
    tor_address = "pg6mmjiyjmcrsslvykfwnntlaru7p5svn6y2ymmju6nubxndf4pscryd.onion"

    node.rpc.call("setban", [tor_address, "add"])
    banned = node.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert any(entry["address"] == tor_address for entry in banned)

    node.rpc.call("setban", [tor_address, "remove"])
    assert node.rpc.call("listbanned") == []


def bantime_given_at_a_restart_sets_a_new_ban_s_duration(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: a ban added after `-bantime=1234` lasts that long.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.BAN, node.capabilities, skip_counts)

    node.restart(["-bantime=1234"])
    node.rpc.call("setban", ["127.0.0.1", "add"])
    banned = node.rpc.call("listbanned")
    assert isinstance(banned, list)
    assert banned[0]["ban_duration"] == 1234
