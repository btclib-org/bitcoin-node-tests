# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_feefilter`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_feefilter.py`:
`p2p_feefilter_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_feefilter_test import (
    feefilter_filters_announcements,
    feefilter_is_not_sent_in_blocks_only_mode,
    feefilter_is_not_sent_to_a_block_relay_only_peer,
    feefilter_is_not_sent_to_a_forcerelay_peer,
    feefilter_is_sent_to_an_inbound_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_feefilter_is_sent_to_an_inbound_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    feefilter_is_sent_to_an_inbound_peer(bitcoind_cluster)


def test_feefilter_is_not_sent_to_a_forcerelay_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    feefilter_is_not_sent_to_a_forcerelay_peer(bitcoind_cluster)


def test_feefilter_filters_announcements(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    feefilter_filters_announcements(bitcoind_cluster, skip_counts)


def test_feefilter_is_not_sent_to_a_block_relay_only_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    feefilter_is_not_sent_to_a_block_relay_only_peer(bitcoind_cluster, skip_counts)


def test_feefilter_is_not_sent_in_blocks_only_mode(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    feefilter_is_not_sent_in_blocks_only_mode(bitcoind_cluster, skip_counts)
