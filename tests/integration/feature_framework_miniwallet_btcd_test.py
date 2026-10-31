# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_framework_miniwallet`, on tf2's own harness: btcd.

`feature_framework_miniwallet_test.py` beside this module is the body,
run here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_framework_miniwallet_btcd_test.py
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
    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(btcd_adapter, skip_counts)


def test_mini_wallet_spends_two_coins_in_a_row(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mini_wallet_spends_two_coins_in_a_row(btcd_adapter, skip_counts)


def test_mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
        btcd_adapter, skip_counts
    )


def test_mini_wallet_fee_rate_is_the_fee_the_node_reports(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mini_wallet_fee_rate_is_the_fee_the_node_reports(btcd_adapter, skip_counts)


def test_mini_wallet_version_3_is_held_to_truc_policy(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mini_wallet_version_3_is_held_to_truc_policy(btcd_adapter, skip_counts)
