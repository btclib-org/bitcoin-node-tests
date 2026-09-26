# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_framework_miniwallet`, on tf2's own harness: btclib-node.

The same request `feature_framework_miniwallet_bitcoind_test.py` makes,
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` is not declared
(`btclib_node.py`'s own docstring is why: a solo node never leaves
`NodeStatus.SyncingHeaders`, ISS btclib-node#1071), so this is a counted
skip rather than a run -- `mini_wallet.py`'s own docstring has why no
other delivery of the mined block avoids it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_framework_miniwallet_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_mini_wallet_spends_two_coins_in_a_row(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_mini_wallet_fee_rate_is_the_fee_the_node_reports(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_mini_wallet_version_3_is_held_to_truc_policy(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
