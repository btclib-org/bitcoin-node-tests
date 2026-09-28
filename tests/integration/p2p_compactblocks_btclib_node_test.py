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


def test_a_low_work_cmpctblock_is_ignored(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    a_low_work_cmpctblock_is_ignored(btclib_node_cluster, skip_counts)


def test_a_low_work_cmpctblock_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    a_low_work_cmpctblock_is_logged(btclib_node_cluster, skip_counts)


def test_a_second_blocktxn_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    a_second_blocktxn_drops_the_peer(btclib_node_cluster, skip_counts)


def test_a_second_blocktxn_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    a_second_blocktxn_is_logged(btclib_node_cluster, skip_counts)


def test_a_stalling_peer_leaves_the_block_to_another(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_stalling_peer_leaves_the_block_to_another(btclib_node_cluster, skip_counts)


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


def test_an_empty_getblocktxn_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    an_empty_getblocktxn_drops_the_peer(btclib_node_cluster)


def test_an_empty_getblocktxn_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    an_empty_getblocktxn_is_logged(btclib_node_cluster, skip_counts)


def test_an_invalid_cmpctblock_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_invalid_cmpctblock_drops_the_peer(btclib_node_cluster, skip_counts)


def test_an_invalid_sendcmpct_announce_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    an_invalid_sendcmpct_announce_drops_the_peer(btclib_node_cluster)


def test_an_invalid_sendcmpct_announce_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    an_invalid_sendcmpct_announce_is_logged(btclib_node_cluster, skip_counts)


def test_getblocktxn_is_answered_near_the_tip(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getblocktxn_is_answered_near_the_tip(btclib_node_cluster, skip_counts)


def test_getpeerinfo_reports_high_bandwidth_states(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getpeerinfo_reports_high_bandwidth_states(btclib_node_cluster, skip_counts)


def test_invalid_transactions_in_a_cmpctblock_keep_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    invalid_transactions_in_a_cmpctblock_keep_the_peer(btclib_node_cluster, skip_counts)


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


def test_sendcmpct_negotiates_over_an_outbound_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendcmpct_negotiates_over_an_outbound_peer(btclib_node_cluster, skip_counts)


def test_the_last_reconstruction_is_kept_for_an_outbound_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    the_last_reconstruction_is_kept_for_an_outbound_peer(
        btclib_node_cluster, skip_counts
    )


def test_unsolicited_cmpctblocks_are_ignored(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    unsolicited_cmpctblocks_are_ignored(btclib_node_cluster, skip_counts)
