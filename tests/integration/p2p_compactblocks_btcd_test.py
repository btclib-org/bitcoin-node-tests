# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks`, rewritten on tf2's own harness: btcd.

`p2p_compactblocks_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_compactblocks_btcd_test.py
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
    a_stalling_peer_leaves_the_block_to_another,
    a_submitted_block_is_announced_compact,
    a_wrong_blocktxn_falls_back_to_the_block,
    an_announced_block_is_asked_for_compact,
    an_empty_getblocktxn_drops_the_peer,
    an_empty_getblocktxn_is_logged,
    an_invalid_cmpctblock_drops_the_peer,
    an_invalid_optimistic_cmpctblock_drops_the_peer,
    an_invalid_sendcmpct_announce_drops_the_peer,
    an_invalid_sendcmpct_announce_is_logged,
    getblocktxn_is_answered_near_the_tip,
    getpeerinfo_reports_high_bandwidth_states,
    invalid_transactions_in_a_cmpctblock_keep_the_peer,
    only_missing_transactions_are_asked_for,
    sendcmpct_negotiates_compact_announcements,
    sendcmpct_negotiates_over_an_outbound_peer,
    the_last_reconstruction_is_kept_for_an_outbound_peer,
    unsolicited_cmpctblocks_are_ignored,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_off_the_tip_is_not_sent_compact(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_block_off_the_tip_is_not_sent_compact(btcd_cluster, skip_counts)


def test_a_compact_block_is_built_as_bip152_says(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_compact_block_is_built_as_bip152_says(btcd_cluster, skip_counts)


def test_a_low_work_cmpctblock_is_ignored(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    a_low_work_cmpctblock_is_ignored(btcd_cluster, skip_counts)


def test_a_low_work_cmpctblock_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    a_low_work_cmpctblock_is_logged(btcd_cluster, skip_counts)


def test_a_second_blocktxn_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    a_second_blocktxn_drops_the_peer(btcd_cluster, skip_counts)


def test_a_second_blocktxn_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    a_second_blocktxn_is_logged(btcd_cluster, skip_counts)


def test_a_stalling_peer_leaves_the_block_to_another(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_stalling_peer_leaves_the_block_to_another(btcd_cluster, skip_counts)


def test_a_submitted_block_is_announced_compact(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_submitted_block_is_announced_compact(btcd_cluster, skip_counts)


def test_a_wrong_blocktxn_falls_back_to_the_block(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_wrong_blocktxn_falls_back_to_the_block(btcd_cluster, skip_counts)


def test_an_announced_block_is_asked_for_compact(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_announced_block_is_asked_for_compact(btcd_cluster, skip_counts)


def test_an_empty_getblocktxn_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
) -> None:
    """The target: the wire half the body module names, over btcd."""
    an_empty_getblocktxn_drops_the_peer(btcd_cluster)


def test_an_empty_getblocktxn_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    an_empty_getblocktxn_is_logged(btcd_cluster, skip_counts)


def test_an_invalid_cmpctblock_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_invalid_cmpctblock_drops_the_peer(btcd_cluster, skip_counts)


def test_an_invalid_optimistic_cmpctblock_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_invalid_optimistic_cmpctblock_drops_the_peer(btcd_cluster, skip_counts)


def test_an_invalid_sendcmpct_announce_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
) -> None:
    """The target: the wire half the body module names, over btcd."""
    an_invalid_sendcmpct_announce_drops_the_peer(btcd_cluster)


def test_an_invalid_sendcmpct_announce_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    an_invalid_sendcmpct_announce_is_logged(btcd_cluster, skip_counts)


def test_getblocktxn_is_answered_near_the_tip(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getblocktxn_is_answered_near_the_tip(btcd_cluster, skip_counts)


def test_getpeerinfo_reports_high_bandwidth_states(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getpeerinfo_reports_high_bandwidth_states(btcd_cluster, skip_counts)


def test_invalid_transactions_in_a_cmpctblock_keep_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    invalid_transactions_in_a_cmpctblock_keep_the_peer(btcd_cluster, skip_counts)


def test_only_missing_transactions_are_asked_for(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    only_missing_transactions_are_asked_for(btcd_cluster, skip_counts)


def test_sendcmpct_negotiates_compact_announcements(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendcmpct_negotiates_compact_announcements(btcd_cluster, skip_counts)


def test_sendcmpct_negotiates_over_an_outbound_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendcmpct_negotiates_over_an_outbound_peer(btcd_cluster, skip_counts)


def test_the_last_reconstruction_is_kept_for_an_outbound_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    the_last_reconstruction_is_kept_for_an_outbound_peer(btcd_cluster, skip_counts)


def test_unsolicited_cmpctblocks_are_ignored(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    unsolicited_cmpctblocks_are_ignored(btcd_cluster, skip_counts)
