# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_opportunistic_1p1c`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/p2p_opportunistic_1p1c.py`:
`p2p_opportunistic_1p1c_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_package_is_taken_in_on_top_of_another(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_package_is_taken_in_on_top_of_another(bitcoind_cluster, skip_counts)


def test_a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
        bitcoind_cluster, skip_counts
    )


def test_a_rejected_parent_is_taken_in_with_its_child(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_parent_is_taken_in_with_its_child(bitcoind_cluster, skip_counts)


def test_a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
        bitcoind_cluster, skip_counts
    )


def test_a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
        bitcoind_cluster, skip_counts
    )


def test_an_invalid_parent_from_another_peer_leaves_the_orphan(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_invalid_parent_from_another_peer_leaves_the_orphan(bitcoind_cluster, skip_counts)


def test_an_orphan_is_taken_in_with_its_low_fee_parent(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_orphan_is_taken_in_with_its_low_fee_parent(bitcoind_cluster, skip_counts)


def test_an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
        bitcoind_cluster, skip_counts
    )


def test_no_rejected_parent_of_a_two_parent_orphan_is_requested(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    no_rejected_parent_of_a_two_parent_orphan_is_requested(
        bitcoind_cluster, skip_counts
    )


def test_parent_and_child_are_evaluated_together_only_from_one_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    parent_and_child_are_evaluated_together_only_from_one_peer(
        bitcoind_cluster, skip_counts
    )
