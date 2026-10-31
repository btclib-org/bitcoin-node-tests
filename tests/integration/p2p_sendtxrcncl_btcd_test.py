# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_sendtxrcncl`, rewritten on tf2's own harness: btcd.

`p2p_sendtxrcncl_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_sendtxrcncl_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_sendtxrcncl_test import (
    sendtxrcncl_is_ignored_without_the_option,
    sendtxrcncl_is_ignored_without_the_option_in_the_log,
    sendtxrcncl_is_not_sent_in_blocks_only_mode,
    sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay,
    sendtxrcncl_is_sent_to_full_relay_outbound_peers,
    sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions,
    sendtxrcncl_kept_peers_are_logged,
    sendtxrcncl_kept_peers_stay_connected,
    sendtxrcncl_on_block_relay_only_is_logged,
    sendtxrcncl_violations_are_logged,
    sendtxrcncl_violations_drop_the_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
        btcd_cluster, skip_counts
    )


def test_sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(btcd_cluster, skip_counts)


def test_sendtxrcncl_is_sent_to_full_relay_outbound_peers(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_sent_to_full_relay_outbound_peers(btcd_cluster, skip_counts)


def test_sendtxrcncl_on_block_relay_only_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_on_block_relay_only_is_logged(btcd_cluster, skip_counts)


def test_sendtxrcncl_is_not_sent_in_blocks_only_mode(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_not_sent_in_blocks_only_mode(btcd_cluster, skip_counts)


def test_sendtxrcncl_is_ignored_without_the_option(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_ignored_without_the_option(btcd_cluster)


def test_sendtxrcncl_is_ignored_without_the_option_in_the_log(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_is_ignored_without_the_option_in_the_log(btcd_cluster, skip_counts)


def test_sendtxrcncl_violations_drop_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_violations_drop_the_peer(btcd_cluster, skip_counts)


def test_sendtxrcncl_violations_are_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_violations_are_logged(btcd_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_stay_connected(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_kept_peers_stay_connected(btcd_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_are_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sendtxrcncl_kept_peers_are_logged(btcd_cluster, skip_counts)
