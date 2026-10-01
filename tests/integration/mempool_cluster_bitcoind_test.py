# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_cluster`, rewritten on this repository's own harness.

Read from Core's `test/functional/mempool_cluster.py`:
`mempool_cluster_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for from `v31.0`
on, the cluster mempool's first release; an older build is a counted skip.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_cluster_test import (
    mempool_limits_clusters_and_reports_their_chunks,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mempool_limits_clusters_and_reports_their_chunks(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mempool_limits_clusters_and_reports_their_chunks(bitcoind_cluster, skip_counts)
