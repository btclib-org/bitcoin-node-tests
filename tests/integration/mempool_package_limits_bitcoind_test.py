# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_limits`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_package_limits.py`:
`mempool_package_limits_test.py` beside this module holds each body, run
here against bitcoind. A bitcoind from before the cluster mempool declares
no `Capability.LIMIT_CLUSTER_COUNT`, and each body is then a counted skip.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_in_package_ancestors_count_toward_the_mempool_ancestor_limit(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    in_package_ancestors_count_toward_the_mempool_ancestor_limit(
        bitcoind_cluster, skip_counts
    )


def test_in_package_descendants_count_toward_the_mempool_descendant_limit(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    in_package_descendants_count_toward_the_mempool_descendant_limit(
        bitcoind_cluster, skip_counts
    )
