# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_getblockstats`, on tf2's own harness: btclib-node.

The same requests `rpc_getblockstats_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.BLOCK_STATS` is not declared (`btclib_node.py`'s own
docstring is why: `getblockstats` names no callback in its dispatch
table, on either build), so every subject is a counted skip on that
capability alone.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_getblockstats_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_genesis_block_statistics(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_op_return_is_counted_but_not_actual(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_selected_stats_narrow_the_answer(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_height_out_of_range(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_invalid_statistic_name(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_unknown_block_hash(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_required_args(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)


def test_block_not_found_on_disk(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.BLOCK_STATS, btclib_node_adapter.capabilities, skip_counts)
