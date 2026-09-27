# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_sendtxrcncl`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_sendtxrcncl.py`:
`p2p_sendtxrcncl_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
        bitcoind_cluster, skip_counts
    )


def test_sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
        bitcoind_cluster, skip_counts
    )


def test_sendtxrcncl_is_sent_to_full_relay_outbound_peers(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_sent_to_full_relay_outbound_peers(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_on_block_relay_only_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_on_block_relay_only_is_logged(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_is_not_sent_in_blocks_only_mode(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_not_sent_in_blocks_only_mode(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_is_ignored_without_the_option(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_ignored_without_the_option(bitcoind_cluster)


def test_sendtxrcncl_is_ignored_without_the_option_in_the_log(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_is_ignored_without_the_option_in_the_log(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_violations_drop_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_violations_drop_the_peer(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_violations_are_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_violations_are_logged(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_stay_connected(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_kept_peers_stay_connected(bitcoind_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_are_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    sendtxrcncl_kept_peers_are_logged(bitcoind_cluster, skip_counts)
