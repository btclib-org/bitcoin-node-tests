# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_framework_miniwallet`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_framework_miniwallet.py`:
`feature_framework_miniwallet_test.py` beside this module holds each
body, run here against bitcoind, which declares every capability they
ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_framework_miniwallet_test import (
    mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones,
    mini_wallet_fee_rate_is_the_fee_the_node_reports,
    mini_wallet_spends_a_coin_it_mined_without_a_node_wallet,
    mini_wallet_spends_two_coins_in_a_row,
    mini_wallet_version_3_is_held_to_truc_policy,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
        bitcoind_adapter, skip_counts
    )


def test_mini_wallet_spends_two_coins_in_a_row(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mini_wallet_spends_two_coins_in_a_row(bitcoind_adapter, skip_counts)


def test_mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
        bitcoind_adapter, skip_counts
    )


def test_mini_wallet_fee_rate_is_the_fee_the_node_reports(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mini_wallet_fee_rate_is_the_fee_the_node_reports(bitcoind_adapter, skip_counts)


def test_mini_wallet_version_3_is_held_to_truc_policy(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mini_wallet_version_3_is_held_to_truc_policy(bitcoind_adapter, skip_counts)
