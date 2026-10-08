# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_cluster`, rewritten on tf2's own harness: btclib-node.

`mempool_cluster_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test is a counted skip on every build, on
`Capability.LIMIT_CLUSTER_SIZE`: `-limitclustersize` is not one of
`cli.py`'s registered options
([ISS btclib-node#1383](https://github.com/btclib-org/btclib-node/issues/1383)).
Neither build declares `Capability.MEMPOOL_GRAPH`
([ISS btclib-node#1501](https://github.com/btclib-org/btclib-node/issues/1501))
or `Capability.CLUSTER_LINEARIZATION` either
([ISS btclib-node#1499](https://github.com/btclib-org/btclib-node/issues/1499)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_cluster_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_cluster_test import (
    mempool_limits_clusters_and_reports_their_chunks,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mempool_limits_clusters_and_reports_their_chunks(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mempool_limits_clusters_and_reports_their_chunks(btclib_node_cluster, skip_counts)
