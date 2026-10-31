# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_rbf`, rewritten on tf2's own harness: btcd.

`mempool_package_rbf_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_package_rbf_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_package_rbf_test import (
    a_child_double_spending_its_mempool_ancestor_is_refused,
    a_child_pays_to_replace_a_single_conflict,
    a_child_pays_to_replace_its_parents_conflicts,
    a_package_must_beat_its_direct_conflicts_feerate,
    a_package_must_pay_more_and_for_its_own_relay,
    a_package_replaces_no_more_clusters_than_the_limit,
    a_package_with_mempool_ancestors_replaces_nothing,
    a_package_with_two_parents_replaces_nothing,
    a_zero_fee_truc_parent_and_its_child_replace_a_package,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_child_pays_to_replace_its_parents_conflicts(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_child_pays_to_replace_its_parents_conflicts(btcd_cluster, skip_counts)


def test_a_child_pays_to_replace_a_single_conflict(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_child_pays_to_replace_a_single_conflict(btcd_cluster, skip_counts)


def test_a_package_must_pay_more_and_for_its_own_relay(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_must_pay_more_and_for_its_own_relay(btcd_cluster, skip_counts)


def test_a_package_replaces_no_more_clusters_than_the_limit(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_replaces_no_more_clusters_than_the_limit(btcd_cluster, skip_counts)


def test_a_package_with_mempool_ancestors_replaces_nothing(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_with_mempool_ancestors_replaces_nothing(btcd_cluster, skip_counts)


def test_a_package_with_two_parents_replaces_nothing(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_with_two_parents_replaces_nothing(btcd_cluster, skip_counts)


def test_a_package_must_beat_its_direct_conflicts_feerate(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_must_beat_its_direct_conflicts_feerate(btcd_cluster, skip_counts)


def test_a_zero_fee_truc_parent_and_its_child_replace_a_package(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_zero_fee_truc_parent_and_its_child_replace_a_package(btcd_cluster, skip_counts)


def test_a_child_double_spending_its_mempool_ancestor_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_child_double_spending_its_mempool_ancestor_is_refused(btcd_cluster, skip_counts)
