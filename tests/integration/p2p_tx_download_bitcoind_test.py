# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_tx_download`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/p2p_tx_download.py`:
`p2p_tx_download_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_tx_download_test import (
    a_disconnect_falls_back_to_another_peer,
    a_large_inv_is_capped_without_the_relay_permission,
    a_noban_peer_is_asked_at_once,
    a_notfound_falls_back_to_another_peer,
    a_ready_preferred_peer_is_asked_first,
    a_rejected_tx_is_asked_for_again_after_a_block,
    a_spurious_notfound_is_ignored,
    a_tx_reaches_a_node_past_unresponsive_peers,
    a_txid_peer_is_asked_at_once_without_a_wtxid_peer,
    a_txid_peer_waits_beside_a_wtxid_peer,
    an_expired_request_falls_back_to_another_peer,
    an_inbound_peer_is_asked_after_the_delay,
    an_inv_of_the_wrong_kind_is_ignored,
    an_outbound_peer_is_asked_at_once,
    duplicate_inv_entries_are_processed_once,
    every_announcing_peer_is_asked_in_turn,
    requests_in_flight_are_capped,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_disconnect_falls_back_to_another_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_disconnect_falls_back_to_another_peer(bitcoind_cluster, skip_counts)


def test_a_large_inv_is_capped_without_the_relay_permission(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_large_inv_is_capped_without_the_relay_permission(bitcoind_cluster, skip_counts)


def test_a_noban_peer_is_asked_at_once(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_noban_peer_is_asked_at_once(bitcoind_cluster, skip_counts)


def test_a_notfound_falls_back_to_another_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_notfound_falls_back_to_another_peer(bitcoind_cluster, skip_counts)


def test_a_ready_preferred_peer_is_asked_first(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_ready_preferred_peer_is_asked_first(bitcoind_cluster, skip_counts)


def test_a_rejected_tx_is_asked_for_again_after_a_block(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_tx_is_asked_for_again_after_a_block(bitcoind_cluster, skip_counts)


def test_a_spurious_notfound_is_ignored(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_spurious_notfound_is_ignored(bitcoind_cluster, skip_counts)


def test_a_tx_reaches_a_node_past_unresponsive_peers(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_tx_reaches_a_node_past_unresponsive_peers(bitcoind_cluster, skip_counts)


def test_a_txid_peer_is_asked_at_once_without_a_wtxid_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_txid_peer_is_asked_at_once_without_a_wtxid_peer(bitcoind_cluster, skip_counts)


def test_a_txid_peer_waits_beside_a_wtxid_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_txid_peer_waits_beside_a_wtxid_peer(bitcoind_cluster, skip_counts)


def test_an_expired_request_falls_back_to_another_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_expired_request_falls_back_to_another_peer(bitcoind_cluster, skip_counts)


def test_an_inbound_peer_is_asked_after_the_delay(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_inbound_peer_is_asked_after_the_delay(bitcoind_cluster, skip_counts)


def test_an_inv_of_the_wrong_kind_is_ignored(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_inv_of_the_wrong_kind_is_ignored(bitcoind_cluster, skip_counts)


def test_an_outbound_peer_is_asked_at_once(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_outbound_peer_is_asked_at_once(bitcoind_cluster, skip_counts)


def test_duplicate_inv_entries_are_processed_once(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    duplicate_inv_entries_are_processed_once(bitcoind_cluster, skip_counts)


def test_every_announcing_peer_is_asked_in_turn(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    every_announcing_peer_is_asked_in_turn(bitcoind_cluster, skip_counts)


def test_requests_in_flight_are_capped(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    requests_in_flight_are_capped(bitcoind_cluster, skip_counts)
