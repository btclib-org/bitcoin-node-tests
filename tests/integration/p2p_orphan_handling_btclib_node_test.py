# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_orphan_handling`, rewritten on tf2's own harness: btclib-node.

`p2p_orphan_handling_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_orphan_handling_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_orphan_handling_test import (
    a_parent_gone_missing_is_requested,
    a_parent_of_the_same_txid_is_requested_again,
    an_inv_by_an_orphan_txid_is_requested,
    an_orphan_is_reconsidered_once_its_parent_is_mined,
    an_orphan_of_the_same_txid_is_kept_too,
    an_outbound_announcer_is_asked_for_parents_first,
    every_announcer_is_asked_for_parents,
    parents_arriving_during_the_delay_are_not_requested,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_parent_gone_missing_is_requested(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_parent_gone_missing_is_requested(btclib_node_cluster, skip_counts)


def test_a_parent_of_the_same_txid_is_requested_again(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_parent_of_the_same_txid_is_requested_again(btclib_node_cluster, skip_counts)


def test_an_inv_by_an_orphan_txid_is_requested(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_inv_by_an_orphan_txid_is_requested(btclib_node_cluster, skip_counts)


def test_an_orphan_is_reconsidered_once_its_parent_is_mined(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_orphan_is_reconsidered_once_its_parent_is_mined(btclib_node_cluster, skip_counts)


def test_an_orphan_of_the_same_txid_is_kept_too(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_orphan_of_the_same_txid_is_kept_too(btclib_node_cluster, skip_counts)


def test_an_outbound_announcer_is_asked_for_parents_first(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_outbound_announcer_is_asked_for_parents_first(btclib_node_cluster, skip_counts)


def test_every_announcer_is_asked_for_parents(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    every_announcer_is_asked_for_parents(btclib_node_cluster, skip_counts)


def test_parents_arriving_during_the_delay_are_not_requested(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    parents_arriving_during_the_delay_are_not_requested(
        btclib_node_cluster, skip_counts
    )
