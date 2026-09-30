# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_opportunistic_1p1c`, rewritten on tf2's own harness: btclib-node.

`p2p_opportunistic_1p1c_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_opportunistic_1p1c_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_opportunistic_1p1c_test import (
    a_package_is_taken_in_on_top_of_another,
    a_rejected_parent_is_taken_in_only_with_a_child_paying_enough,
    a_rejected_parent_is_taken_in_with_its_child,
    a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough,
    a_rejected_parent_with_no_witness_is_taken_in_with_its_child,
    an_invalid_parent_from_another_peer_leaves_the_orphan,
    an_orphan_is_taken_in_with_its_low_fee_parent,
    an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool,
    no_rejected_parent_of_a_two_parent_orphan_is_requested,
    parent_and_child_are_evaluated_together_only_from_one_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_package_is_taken_in_on_top_of_another(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_package_is_taken_in_on_top_of_another(btclib_node_cluster, skip_counts)


def test_a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
        btclib_node_cluster, skip_counts
    )


def test_a_rejected_parent_is_taken_in_with_its_child(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_rejected_parent_is_taken_in_with_its_child(btclib_node_cluster, skip_counts)


def test_a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
        btclib_node_cluster, skip_counts
    )


def test_a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
        btclib_node_cluster, skip_counts
    )


def test_an_invalid_parent_from_another_peer_leaves_the_orphan(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_invalid_parent_from_another_peer_leaves_the_orphan(
        btclib_node_cluster, skip_counts
    )


def test_an_orphan_is_taken_in_with_its_low_fee_parent(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_orphan_is_taken_in_with_its_low_fee_parent(btclib_node_cluster, skip_counts)


def test_an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
        btclib_node_cluster, skip_counts
    )


def test_no_rejected_parent_of_a_two_parent_orphan_is_requested(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    no_rejected_parent_of_a_two_parent_orphan_is_requested(
        btclib_node_cluster, skip_counts
    )


def test_parent_and_child_are_evaluated_together_only_from_one_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    parent_and_child_are_evaluated_together_only_from_one_peer(
        btclib_node_cluster, skip_counts
    )
