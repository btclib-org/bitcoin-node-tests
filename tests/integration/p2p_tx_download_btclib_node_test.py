# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_tx_download`, rewritten on tf2's own harness: btclib-node.

`p2p_tx_download_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_tx_download_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_disconnect_falls_back_to_another_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_disconnect_falls_back_to_another_peer(btclib_node_cluster, skip_counts)


def test_a_large_inv_is_capped_without_the_relay_permission(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_large_inv_is_capped_without_the_relay_permission(btclib_node_cluster, skip_counts)


def test_a_noban_peer_is_asked_at_once(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_noban_peer_is_asked_at_once(btclib_node_cluster, skip_counts)


def test_a_notfound_falls_back_to_another_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_notfound_falls_back_to_another_peer(btclib_node_cluster, skip_counts)


def test_a_ready_preferred_peer_is_asked_first(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_ready_preferred_peer_is_asked_first(btclib_node_cluster, skip_counts)


def test_a_rejected_tx_is_asked_for_again_after_a_block(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_rejected_tx_is_asked_for_again_after_a_block(btclib_node_cluster, skip_counts)


def test_a_spurious_notfound_is_ignored(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_spurious_notfound_is_ignored(btclib_node_cluster, skip_counts)


def test_a_tx_reaches_a_node_past_unresponsive_peers(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_tx_reaches_a_node_past_unresponsive_peers(btclib_node_cluster, skip_counts)


def test_a_txid_peer_is_asked_at_once_without_a_wtxid_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_txid_peer_is_asked_at_once_without_a_wtxid_peer(btclib_node_cluster, skip_counts)


def test_a_txid_peer_waits_beside_a_wtxid_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_txid_peer_waits_beside_a_wtxid_peer(btclib_node_cluster, skip_counts)


def test_an_expired_request_falls_back_to_another_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_expired_request_falls_back_to_another_peer(btclib_node_cluster, skip_counts)


def test_an_inbound_peer_is_asked_after_the_delay(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_inbound_peer_is_asked_after_the_delay(btclib_node_cluster, skip_counts)


def test_an_inv_of_the_wrong_kind_is_ignored(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_inv_of_the_wrong_kind_is_ignored(btclib_node_cluster, skip_counts)


def test_an_outbound_peer_is_asked_at_once(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_outbound_peer_is_asked_at_once(btclib_node_cluster, skip_counts)


def test_duplicate_inv_entries_are_processed_once(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    duplicate_inv_entries_are_processed_once(btclib_node_cluster, skip_counts)


def test_every_announcing_peer_is_asked_in_turn(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    every_announcing_peer_is_asked_in_turn(btclib_node_cluster, skip_counts)


def test_requests_in_flight_are_capped(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    requests_in_flight_are_capped(btclib_node_cluster, skip_counts)
