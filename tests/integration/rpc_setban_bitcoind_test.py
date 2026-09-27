# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, rewritten on this repository's own harness.

Read from Core's `test/functional/rpc_setban.py`: `rpc_setban_test.py`
beside this module holds each body, run here against bitcoind, which
declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_ban_drops_the_connection_it_matches(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_ban_drops_the_connection_it_matches(bitcoind_cluster, skip_counts)


def test_a_ban_survives_a_restart_until_it_is_removed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_ban_survives_a_restart_until_it_is_removed(bitcoind_cluster, skip_counts)


def test_a_noban_permission_reconnects_a_banned_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_noban_permission_reconnects_a_banned_peer(bitcoind_cluster, skip_counts)


def test_a_non_ip_address_can_be_banned_and_unbanned(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_non_ip_address_can_be_banned_and_unbanned(bitcoind_cluster, skip_counts)


def test_bantime_given_at_a_restart_sets_a_new_ban_s_duration(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    bantime_given_at_a_restart_sets_a_new_ban_s_duration(bitcoind_cluster, skip_counts)
