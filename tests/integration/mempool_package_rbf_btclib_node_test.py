# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_rbf`, rewritten on tf2's own harness: btclib-node.

`mempool_package_rbf_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on
`Capability.PACKAGE_ACCEPTANCE` where the build does not declare it
(`btclib_node.py`'s own docstring). A build that does fails the replacement
bodies, the replacement `submitpackage` makes being refused
([ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_package_rbf_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_child_pays_to_replace_its_parents_conflicts(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_child_pays_to_replace_its_parents_conflicts(btclib_node_cluster, skip_counts)


def test_a_child_pays_to_replace_a_single_conflict(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_child_pays_to_replace_a_single_conflict(btclib_node_cluster, skip_counts)


def test_a_package_must_pay_more_and_for_its_own_relay(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_must_pay_more_and_for_its_own_relay(btclib_node_cluster, skip_counts)


def test_a_package_replaces_no_more_clusters_than_the_limit(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_replaces_no_more_clusters_than_the_limit(btclib_node_cluster, skip_counts)


def test_a_package_with_mempool_ancestors_replaces_nothing(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_with_mempool_ancestors_replaces_nothing(btclib_node_cluster, skip_counts)


def test_a_package_with_two_parents_replaces_nothing(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_with_two_parents_replaces_nothing(btclib_node_cluster, skip_counts)


def test_a_package_must_beat_its_direct_conflicts_feerate(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_must_beat_its_direct_conflicts_feerate(btclib_node_cluster, skip_counts)


def test_a_zero_fee_truc_parent_and_its_child_replace_a_package(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_zero_fee_truc_parent_and_its_child_replace_a_package(
        btclib_node_cluster, skip_counts
    )


def test_a_child_double_spending_its_mempool_ancestor_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_child_double_spending_its_mempool_ancestor_is_refused(
        btclib_node_cluster, skip_counts
    )
