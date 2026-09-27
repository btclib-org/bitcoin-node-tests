# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex_init`, rewritten on this repository's own harness.

Read from Core's `test/functional/feature_reindex_init.py`:
`feature_reindex_init_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_reindex_init_test import (
    a_lost_block_index_is_rebuilt_once_allowed,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_lost_block_index_is_rebuilt_once_allowed(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the refusal and the reindex, over bitcoind."""
    a_lost_block_index_is_rebuilt_once_allowed(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
