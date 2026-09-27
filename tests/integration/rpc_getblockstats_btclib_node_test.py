# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockstats`, rewritten on this harness: btclib-node.

`rpc_getblockstats_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.BLOCK_STATS` is not declared
(`btclib_node.py`'s own docstring is why: `getblockstats` names no
callback in its dispatch table, on either build), so every test is a
counted skip on that capability, asked before any other.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_getblockstats_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.rpc_getblockstats_test import (
    block_not_found_on_disk,
    genesis_block_statistics,
    height_out_of_range,
    invalid_statistic_name,
    op_return_is_counted_but_not_actual,
    required_args,
    selected_stats_narrow_the_answer,
    unknown_block_hash,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_genesis_block_statistics(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    genesis_block_statistics(btclib_node_adapter, skip_counts)


def test_op_return_is_counted_but_not_actual(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    op_return_is_counted_but_not_actual(btclib_node_adapter, skip_counts)


def test_selected_stats_narrow_the_answer(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    selected_stats_narrow_the_answer(btclib_node_adapter, skip_counts)


def test_height_out_of_range(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    height_out_of_range(btclib_node_adapter, skip_counts)


def test_invalid_statistic_name(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    invalid_statistic_name(btclib_node_adapter, skip_counts)


def test_unknown_block_hash(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    unknown_block_hash(btclib_node_adapter, skip_counts)


def test_required_args(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    required_args(btclib_node_adapter, skip_counts)


def test_block_not_found_on_disk(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    block_not_found_on_disk(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
