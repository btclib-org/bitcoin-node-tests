# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_opportunistic_1p1c`, rewritten on tf2's own harness: btcd.

`p2p_opportunistic_1p1c_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_opportunistic_1p1c_btcd_test.py
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
    an_orphan_outlives_large_orphans_from_other_peers,
    an_orphan_outlives_many_orphans_from_other_peers,
    no_rejected_parent_of_a_two_parent_orphan_is_requested,
    parent_and_child_are_evaluated_together_only_from_one_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_package_is_taken_in_on_top_of_another(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_package_is_taken_in_on_top_of_another(btcd_cluster, skip_counts)


def test_a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
        btcd_cluster, skip_counts
    )


def test_a_rejected_parent_is_taken_in_with_its_child(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_parent_is_taken_in_with_its_child(btcd_cluster, skip_counts)


def test_a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
        btcd_cluster, skip_counts
    )


def test_a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
        btcd_cluster, skip_counts
    )


def test_an_invalid_parent_from_another_peer_leaves_the_orphan(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_invalid_parent_from_another_peer_leaves_the_orphan(btcd_cluster, skip_counts)


def test_an_orphan_is_taken_in_with_its_low_fee_parent(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_orphan_is_taken_in_with_its_low_fee_parent(btcd_cluster, skip_counts)


def test_an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
        btcd_cluster, skip_counts
    )


def test_an_orphan_outlives_large_orphans_from_other_peers(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_orphan_outlives_large_orphans_from_other_peers(btcd_cluster, skip_counts)


def test_an_orphan_outlives_many_orphans_from_other_peers(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_orphan_outlives_many_orphans_from_other_peers(btcd_cluster, skip_counts)


def test_no_rejected_parent_of_a_two_parent_orphan_is_requested(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    no_rejected_parent_of_a_two_parent_orphan_is_requested(btcd_cluster, skip_counts)


def test_parent_and_child_are_evaluated_together_only_from_one_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    parent_and_child_are_evaluated_together_only_from_one_peer(
        btcd_cluster, skip_counts
    )
