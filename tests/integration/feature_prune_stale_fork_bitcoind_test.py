# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_prune_stale_fork`, rewritten on this harness.

Read from Core's `test/functional/feature_prune_stale_fork.py`:
`feature_prune_stale_fork_test.py` beside this module is the
body, run here against bitcoind, which declares every capability it asks
for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_prune_stale_fork_test import (
    a_pruned_stale_fork_survives_a_restart,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_pruned_stale_fork_survives_a_restart(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a pruned stale fork survives a restart, over bitcoind."""
    a_pruned_stale_fork_survives_a_restart(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
