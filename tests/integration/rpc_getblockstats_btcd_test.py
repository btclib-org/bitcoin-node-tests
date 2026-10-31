# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockstats`, rewritten on tf2's own harness: btcd.

`rpc_getblockstats_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_getblockstats_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
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

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_genesis_block_statistics(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    genesis_block_statistics(btcd_adapter, skip_counts)


def test_op_return_is_counted_but_not_actual(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    op_return_is_counted_but_not_actual(btcd_adapter, skip_counts)


def test_selected_stats_narrow_the_answer(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    selected_stats_narrow_the_answer(btcd_adapter, skip_counts)


def test_height_out_of_range(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    height_out_of_range(btcd_adapter, skip_counts)


def test_invalid_statistic_name(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    invalid_statistic_name(btcd_adapter, skip_counts)


def test_unknown_block_hash(btcd_adapter: BtcdAdapter, skip_counts: SkipCounts) -> None:
    """The target: the body of the same name, over btcd."""
    unknown_block_hash(btcd_adapter, skip_counts)


def test_required_args(btcd_adapter: BtcdAdapter, skip_counts: SkipCounts) -> None:
    """The target: the body of the same name, over btcd."""
    required_args(btcd_adapter, skip_counts)


def test_block_not_found_on_disk(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    block_not_found_on_disk(make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts)
