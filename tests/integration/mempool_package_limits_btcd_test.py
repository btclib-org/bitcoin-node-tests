# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_limits`, rewritten on tf2's own harness: btcd.

`mempool_package_limits_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_package_limits_btcd_test.py
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

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_in_package_ancestors_count_toward_the_mempool_ancestor_limit(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    in_package_ancestors_count_toward_the_mempool_ancestor_limit(
        btcd_cluster, skip_counts
    )


def test_in_package_descendants_count_toward_the_mempool_descendant_limit(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    in_package_descendants_count_toward_the_mempool_descendant_limit(
        btcd_cluster, skip_counts
    )
