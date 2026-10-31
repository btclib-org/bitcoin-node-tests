# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_setban`, rewritten on tf2's own harness: btcd.

`rpc_setban_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_setban_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_ban_drops_the_connection_it_matches(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_ban_drops_the_connection_it_matches(btcd_cluster, skip_counts)


def test_a_ban_survives_a_restart_until_it_is_removed(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_ban_survives_a_restart_until_it_is_removed(btcd_cluster, skip_counts)


def test_a_noban_permission_reconnects_a_banned_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_noban_permission_reconnects_a_banned_peer(btcd_cluster, skip_counts)


def test_a_non_ip_address_can_be_banned_and_unbanned(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_non_ip_address_can_be_banned_and_unbanned(btcd_cluster, skip_counts)


def test_bantime_given_at_a_restart_sets_a_new_ban_s_duration(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    bantime_given_at_a_restart_sets_a_new_ban_s_duration(btcd_cluster, skip_counts)
