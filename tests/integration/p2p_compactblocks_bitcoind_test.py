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
    a_low_work_cmpctblock_is_ignored,
    a_low_work_cmpctblock_is_logged,
    a_second_blocktxn_drops_the_peer,
    a_second_blocktxn_is_logged,
    a_submitted_block_is_announced_compact,
    a_wrong_blocktxn_falls_back_to_the_block,
    an_announced_block_is_asked_for_compact,
    an_empty_getblocktxn_drops_the_peer,
    an_empty_getblocktxn_is_logged,
    an_invalid_cmpctblock_drops_the_peer,
    an_invalid_sendcmpct_announce_drops_the_peer,
    an_invalid_sendcmpct_announce_is_logged,
    getblocktxn_is_answered_near_the_tip,
    invalid_transactions_in_a_cmpctblock_keep_the_peer,
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


def test_a_low_work_cmpctblock_is_ignored(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    a_low_work_cmpctblock_is_ignored(bitcoind_cluster, skip_counts)


def test_a_low_work_cmpctblock_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    a_low_work_cmpctblock_is_logged(bitcoind_cluster, skip_counts)


def test_a_second_blocktxn_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    a_second_blocktxn_drops_the_peer(bitcoind_cluster, skip_counts)


def test_a_second_blocktxn_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    a_second_blocktxn_is_logged(bitcoind_cluster, skip_counts)


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


def test_an_empty_getblocktxn_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    an_empty_getblocktxn_drops_the_peer(bitcoind_cluster)


def test_an_empty_getblocktxn_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    an_empty_getblocktxn_is_logged(bitcoind_cluster, skip_counts)


def test_an_invalid_cmpctblock_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_invalid_cmpctblock_drops_the_peer(bitcoind_cluster, skip_counts)


def test_an_invalid_sendcmpct_announce_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    an_invalid_sendcmpct_announce_drops_the_peer(bitcoind_cluster)


def test_an_invalid_sendcmpct_announce_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    an_invalid_sendcmpct_announce_is_logged(bitcoind_cluster, skip_counts)


def test_getblocktxn_is_answered_near_the_tip(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getblocktxn_is_answered_near_the_tip(bitcoind_cluster, skip_counts)


def test_invalid_transactions_in_a_cmpctblock_keep_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    invalid_transactions_in_a_cmpctblock_keep_the_peer(bitcoind_cluster, skip_counts)


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
