# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_package_limits`, rewritten on this harness: btclib-node.

`mempool_package_limits_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.LIMIT_CLUSTER_COUNT` is declared
for no build, so each body is a counted skip on it before the node is
restarted.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/mempool_package_limits_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_package_limits_test import (
    in_package_ancestors_count_toward_the_mempool_ancestor_limit,
    in_package_descendants_count_toward_the_mempool_descendant_limit,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_in_package_ancestors_count_toward_the_mempool_ancestor_limit(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    in_package_ancestors_count_toward_the_mempool_ancestor_limit(
        btclib_node_cluster, skip_counts
    )


def test_in_package_descendants_count_toward_the_mempool_descendant_limit(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    in_package_descendants_count_toward_the_mempool_descendant_limit(
        btclib_node_cluster, skip_counts
    )
