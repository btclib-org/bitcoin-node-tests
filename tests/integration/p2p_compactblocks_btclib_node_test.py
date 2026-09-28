# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks`, rewritten on tf2's own harness: btclib-node.

`p2p_compactblocks_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_compactblocks_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_compactblocks_test import (
    a_block_off_the_tip_is_not_sent_compact,
    a_compact_block_is_built_as_bip152_says,
    a_submitted_block_is_announced_compact,
    a_wrong_blocktxn_falls_back_to_the_block,
    an_announced_block_is_asked_for_compact,
    getblocktxn_is_answered_near_the_tip,
    only_missing_transactions_are_asked_for,
    sendcmpct_negotiates_compact_announcements,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_off_the_tip_is_not_sent_compact(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_block_off_the_tip_is_not_sent_compact(btclib_node_cluster, skip_counts)


def test_a_compact_block_is_built_as_bip152_says(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_compact_block_is_built_as_bip152_says(btclib_node_cluster, skip_counts)


def test_a_submitted_block_is_announced_compact(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_submitted_block_is_announced_compact(btclib_node_cluster, skip_counts)


def test_a_wrong_blocktxn_falls_back_to_the_block(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_wrong_blocktxn_falls_back_to_the_block(btclib_node_cluster, skip_counts)


def test_an_announced_block_is_asked_for_compact(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_announced_block_is_asked_for_compact(btclib_node_cluster, skip_counts)


def test_getblocktxn_is_answered_near_the_tip(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getblocktxn_is_answered_near_the_tip(btclib_node_cluster, skip_counts)


def test_only_missing_transactions_are_asked_for(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    only_missing_transactions_are_asked_for(btclib_node_cluster, skip_counts)


def test_sendcmpct_negotiates_compact_announcements(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendcmpct_negotiates_compact_announcements(btclib_node_cluster, skip_counts)
