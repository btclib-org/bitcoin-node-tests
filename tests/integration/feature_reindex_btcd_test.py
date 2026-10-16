# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex`, rewritten on tf2's own harness: btcd.

`feature_reindex_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_reindex_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
from tests.integration.feature_reindex_test import (
    a_reindex_restores_the_height,
    an_interrupted_reindex_keeps_its_index,
    blocks_out_of_order_are_reindexed,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_reindex_restores_the_height(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: each reindex back at the height mined, over btcd."""
    a_reindex_restores_the_height(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_blocks_out_of_order_are_reindexed(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: two blocks swapped on disk reindexed, over btcd."""
    blocks_out_of_order_are_reindexed(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_an_interrupted_reindex_keeps_its_index(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a stopped reindex's filter index kept, over btcd."""
    an_interrupted_reindex_keeps_its_index(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
