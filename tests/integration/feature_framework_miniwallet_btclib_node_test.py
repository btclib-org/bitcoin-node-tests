# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_framework_miniwallet`, on tf2's own harness: btclib-node.

`feature_framework_miniwallet_test.py` beside this module holds each
body, run here against the target rather than the oracle (rule 3 of
issue btclib-org/btclib#2220). `Capability.MINE` is declared only by a
build that connects a submitted block with no peer (`btclib_node.py`'s
own docstring): a build without it is a counted skip before any block is
mined, and a build declaring it runs each scenario but `confirmed_only`,
which asks for `Capability.GENERATE` first and skips on it on every
build (`btclib_node.py`'s own docstring has why).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_framework_miniwallet_btclib_node_test.py
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
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
        btclib_node_adapter, skip_counts
    )


def test_mini_wallet_spends_two_coins_in_a_row(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mini_wallet_spends_two_coins_in_a_row(btclib_node_adapter, skip_counts)


def test_mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
        btclib_node_adapter, skip_counts
    )


def test_mini_wallet_fee_rate_is_the_fee_the_node_reports(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mini_wallet_fee_rate_is_the_fee_the_node_reports(btclib_node_adapter, skip_counts)


def test_mini_wallet_version_3_is_held_to_truc_policy(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mini_wallet_version_3_is_held_to_truc_policy(btclib_node_adapter, skip_counts)
