# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex`, rewritten on this repository's own harness.

Read from Core's `test/functional/feature_reindex.py`:
`feature_reindex_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
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
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: each reindex back at the height mined, over bitcoind."""
    a_reindex_restores_the_height(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_blocks_out_of_order_are_reindexed(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: two blocks swapped on disk reindexed, over bitcoind."""
    blocks_out_of_order_are_reindexed(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_an_interrupted_reindex_keeps_its_index(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a stopped reindex's filter index not wiped, over bitcoind."""
    an_interrupted_reindex_keeps_its_index(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
