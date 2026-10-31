# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_tx_download`, rewritten on tf2's own harness: btcd.

`p2p_tx_download_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

The `relay` permission check is left out: btcd's `--whitelist` takes an
address and grants the one permission `noban` stands for, so there is no
`relay` permission to give or withhold.

The disconnect and `notfound` checks fail against btcd, a deliberate
difference
([ISS 487](https://github.com/btclib-org/btclib-functional-tests/issues/487)):
btcd asks the other peer for the transaction only once that peer
announces it again, after a disconnect
([`netsync/manager.go#L529-L534`](https://github.com/btcsuite/btcd/blob/v0.26.2/netsync/manager.go#L529-L534))
as after a `notfound`
([`netsync/manager.go#L1036-L1039`](https://github.com/btcsuite/btcd/blob/v0.26.2/netsync/manager.go#L1036-L1039)).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_tx_download_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_tx_download_test import (
    a_disconnect_falls_back_to_another_peer,
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_disconnect_falls_back_to_another_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_disconnect_falls_back_to_another_peer(btcd_cluster, skip_counts)


def test_a_noban_peer_is_asked_at_once(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_noban_peer_is_asked_at_once(btcd_cluster, skip_counts)


def test_a_notfound_falls_back_to_another_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_notfound_falls_back_to_another_peer(btcd_cluster, skip_counts)


def test_a_ready_preferred_peer_is_asked_first(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_ready_preferred_peer_is_asked_first(btcd_cluster, skip_counts)


def test_a_rejected_tx_is_asked_for_again_after_a_block(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_tx_is_asked_for_again_after_a_block(btcd_cluster, skip_counts)


def test_a_spurious_notfound_is_ignored(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_spurious_notfound_is_ignored(btcd_cluster, skip_counts)


def test_a_tx_reaches_a_node_past_unresponsive_peers(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_tx_reaches_a_node_past_unresponsive_peers(btcd_cluster, skip_counts)


def test_a_txid_peer_is_asked_at_once_without_a_wtxid_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_txid_peer_is_asked_at_once_without_a_wtxid_peer(btcd_cluster, skip_counts)


def test_a_txid_peer_waits_beside_a_wtxid_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_txid_peer_waits_beside_a_wtxid_peer(btcd_cluster, skip_counts)


def test_an_expired_request_falls_back_to_another_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_expired_request_falls_back_to_another_peer(btcd_cluster, skip_counts)


def test_an_inbound_peer_is_asked_after_the_delay(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_inbound_peer_is_asked_after_the_delay(btcd_cluster, skip_counts)


def test_an_inv_of_the_wrong_kind_is_ignored(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_inv_of_the_wrong_kind_is_ignored(btcd_cluster, skip_counts)


def test_an_outbound_peer_is_asked_at_once(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_outbound_peer_is_asked_at_once(btcd_cluster, skip_counts)


def test_duplicate_inv_entries_are_processed_once(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    duplicate_inv_entries_are_processed_once(btcd_cluster, skip_counts)


def test_every_announcing_peer_is_asked_in_turn(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    every_announcing_peer_is_asked_in_turn(btcd_cluster, skip_counts)


def test_requests_in_flight_are_capped(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    requests_in_flight_are_capped(btcd_cluster, skip_counts)
