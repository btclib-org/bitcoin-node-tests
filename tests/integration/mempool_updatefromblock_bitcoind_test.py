# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_updatefromblock`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_updatefromblock.py`:
`mempool_updatefromblock_test.py` beside this module holds each body,
run here against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reorg_recomputes_every_entry_s_own_ancestors_and_descendants(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    reorg_recomputes_every_entry_s_own_ancestors_and_descendants(
        bitcoind_cluster, skip_counts
    )


def test_a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit(
        bitcoind_cluster, skip_counts
    )
