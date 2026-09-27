# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex_readonly`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_reindex_readonly.py`:
`feature_reindex_readonly_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_reindex_readonly_test import (
    a_read_only_block_file_is_reindexed,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_read_only_block_file_is_reindexed(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a read-only block file reindexed, over bitcoind."""
    a_read_only_block_file_is_reindexed(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
