# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_updatefromblock`, rewritten on this harness: btclib-node.

`mempool_updatefromblock_test.py` beside this module holds each body,
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.LIMIT_CLUSTER_SIZE` is not
declared: measured against `cli.py`'s registered options,
`_build_parser` on the released build and `_OPTIONS` on `main`,
`-limitclustersize` is not one of its registered flags -- a counted skip
on that capability alone, before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_updatefromblock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_updatefromblock_test import (
    a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit,
    reorg_recomputes_every_entry_s_own_ancestors_and_descendants,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reorg_recomputes_every_entry_s_own_ancestors_and_descendants(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    reorg_recomputes_every_entry_s_own_ancestors_and_descendants(
        btclib_node_cluster, skip_counts
    )


def test_a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit(
        btclib_node_cluster, skip_counts
    )
