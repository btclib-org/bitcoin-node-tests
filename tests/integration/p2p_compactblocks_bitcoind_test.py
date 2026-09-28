# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/p2p_compactblocks.py`:
`p2p_compactblocks_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_off_the_tip_is_not_sent_compact(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_block_off_the_tip_is_not_sent_compact(bitcoind_cluster, skip_counts)


def test_a_compact_block_is_built_as_bip152_says(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_compact_block_is_built_as_bip152_says(bitcoind_cluster, skip_counts)


def test_a_submitted_block_is_announced_compact(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_submitted_block_is_announced_compact(bitcoind_cluster, skip_counts)


def test_a_wrong_blocktxn_falls_back_to_the_block(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_wrong_blocktxn_falls_back_to_the_block(bitcoind_cluster, skip_counts)


def test_an_announced_block_is_asked_for_compact(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_announced_block_is_asked_for_compact(bitcoind_cluster, skip_counts)


def test_getblocktxn_is_answered_near_the_tip(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getblocktxn_is_answered_near_the_tip(bitcoind_cluster, skip_counts)


def test_only_missing_transactions_are_asked_for(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    only_missing_transactions_are_asked_for(bitcoind_cluster, skip_counts)


def test_sendcmpct_negotiates_compact_announcements(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendcmpct_negotiates_compact_announcements(bitcoind_cluster, skip_counts)
