# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, rewritten on tf2's own harness: btclib-node.

The same request `rpc_setban_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.BAN` is declared by neither build measured (`btclib_node.py`'s
own docstring), so this skips before a second node or a `setban` call is
ever made.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_setban_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_ban_drops_the_connection_it_matches(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request `rpc_setban_bitcoind_test.py` makes."""
    require(Capability.CONNECT, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.BAN, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_ban_survives_a_restart_until_it_is_removed(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request `rpc_setban_bitcoind_test.py` makes."""
    require(Capability.CONNECT, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.BAN, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_noban_permission_reconnects_a_banned_peer(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request `rpc_setban_bitcoind_test.py` makes."""
    require(Capability.CONNECT, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.BAN, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_non_ip_address_can_be_banned_and_unbanned(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request `rpc_setban_bitcoind_test.py` makes."""
    require(Capability.BAN, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_bantime_given_at_a_restart_sets_a_new_ban_s_duration(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request `rpc_setban_bitcoind_test.py` makes."""
    require(Capability.BAN, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
