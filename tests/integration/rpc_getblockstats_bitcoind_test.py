# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockstats`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getblockstats.py`:
`rpc_getblockstats_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
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
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    genesis_block_statistics(bitcoind_adapter, skip_counts)


def test_op_return_is_counted_but_not_actual(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    op_return_is_counted_but_not_actual(bitcoind_adapter, skip_counts)


def test_selected_stats_narrow_the_answer(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    selected_stats_narrow_the_answer(bitcoind_adapter, skip_counts)


def test_height_out_of_range(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    height_out_of_range(bitcoind_adapter, skip_counts)


def test_invalid_statistic_name(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    invalid_statistic_name(bitcoind_adapter, skip_counts)


def test_unknown_block_hash(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    unknown_block_hash(bitcoind_adapter, skip_counts)


def test_required_args(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    required_args(bitcoind_adapter, skip_counts)


def test_block_not_found_on_disk(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    block_not_found_on_disk(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
