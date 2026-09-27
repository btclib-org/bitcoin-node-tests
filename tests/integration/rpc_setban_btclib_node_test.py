# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, rewritten on tf2's own harness: btclib-node.

`rpc_setban_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.BAN` is declared per build
(`btclib_node.py`'s own docstring): a build without it is a counted skip
before any `setban` call is made, and a build declaring it runs each
scenario whose other capabilities it declares too.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_setban_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_setban_test import (
    a_ban_drops_the_connection_it_matches,
    a_ban_survives_a_restart_until_it_is_removed,
    a_noban_permission_reconnects_a_banned_peer,
    a_non_ip_address_can_be_banned_and_unbanned,
    bantime_given_at_a_restart_sets_a_new_ban_s_duration,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_ban_drops_the_connection_it_matches(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_ban_drops_the_connection_it_matches(btclib_node_cluster, skip_counts)


def test_a_ban_survives_a_restart_until_it_is_removed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_ban_survives_a_restart_until_it_is_removed(btclib_node_cluster, skip_counts)


def test_a_noban_permission_reconnects_a_banned_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_noban_permission_reconnects_a_banned_peer(btclib_node_cluster, skip_counts)


def test_a_non_ip_address_can_be_banned_and_unbanned(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_non_ip_address_can_be_banned_and_unbanned(btclib_node_cluster, skip_counts)


def test_bantime_given_at_a_restart_sets_a_new_ban_s_duration(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    bantime_given_at_a_restart_sets_a_new_ban_s_duration(
        btclib_node_cluster, skip_counts
    )
