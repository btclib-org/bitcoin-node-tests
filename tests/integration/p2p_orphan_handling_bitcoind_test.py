# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_orphan_handling`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/p2p_orphan_handling.py`:
`p2p_orphan_handling_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_orphan_handling_test import (
    a_parent_gone_missing_is_requested,
    a_parent_of_the_same_txid_is_requested_again,
    an_inv_by_an_orphan_txid_is_requested,
    an_orphan_is_reconsidered_once_its_parent_is_mined,
    an_orphan_of_the_same_txid_is_kept_too,
    an_outbound_announcer_is_asked_for_parents_first,
    every_announcer_is_asked_for_parents,
    parents_arriving_during_the_delay_are_not_requested,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_parent_gone_missing_is_requested(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_parent_gone_missing_is_requested(bitcoind_cluster, skip_counts)


def test_a_parent_of_the_same_txid_is_requested_again(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_parent_of_the_same_txid_is_requested_again(bitcoind_cluster, skip_counts)


def test_an_inv_by_an_orphan_txid_is_requested(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_inv_by_an_orphan_txid_is_requested(bitcoind_cluster, skip_counts)


def test_an_orphan_is_reconsidered_once_its_parent_is_mined(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_orphan_is_reconsidered_once_its_parent_is_mined(bitcoind_cluster, skip_counts)


def test_an_orphan_of_the_same_txid_is_kept_too(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_orphan_of_the_same_txid_is_kept_too(bitcoind_cluster, skip_counts)


def test_an_outbound_announcer_is_asked_for_parents_first(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_outbound_announcer_is_asked_for_parents_first(bitcoind_cluster, skip_counts)


def test_every_announcer_is_asked_for_parents(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    every_announcer_is_asked_for_parents(bitcoind_cluster, skip_counts)


def test_parents_arriving_during_the_delay_are_not_requested(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    parents_arriving_during_the_delay_are_not_requested(bitcoind_cluster, skip_counts)
