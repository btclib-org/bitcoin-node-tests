# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_rbf`, rewritten on this repository's own harness.

Read from Core's `test/functional/mempool_package_rbf.py`:
`mempool_package_rbf_test.py` beside this module holds each body, run
here against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_child_pays_to_replace_its_parents_conflicts(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_child_pays_to_replace_its_parents_conflicts(bitcoind_cluster, skip_counts)


def test_a_child_pays_to_replace_a_single_conflict(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_child_pays_to_replace_a_single_conflict(bitcoind_cluster, skip_counts)


def test_a_package_must_pay_more_and_for_its_own_relay(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_must_pay_more_and_for_its_own_relay(bitcoind_cluster, skip_counts)


def test_a_package_replaces_no_more_clusters_than_the_limit(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_replaces_no_more_clusters_than_the_limit(bitcoind_cluster, skip_counts)


def test_a_package_with_mempool_ancestors_replaces_nothing(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_with_mempool_ancestors_replaces_nothing(bitcoind_cluster, skip_counts)


def test_a_package_with_two_parents_replaces_nothing(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_with_two_parents_replaces_nothing(bitcoind_cluster, skip_counts)


def test_a_package_must_beat_its_direct_conflicts_feerate(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_must_beat_its_direct_conflicts_feerate(bitcoind_cluster, skip_counts)


def test_a_zero_fee_truc_parent_and_its_child_replace_a_package(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_zero_fee_truc_parent_and_its_child_replace_a_package(
        bitcoind_cluster, skip_counts
    )


def test_a_child_double_spending_its_mempool_ancestor_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_child_double_spending_its_mempool_ancestor_is_refused(
        bitcoind_cluster, skip_counts
    )
