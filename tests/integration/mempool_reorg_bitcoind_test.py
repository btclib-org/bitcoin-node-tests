# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_reorg`, rewritten on this repository's own harness.

Read from Core's `test/functional/mempool_reorg.py`:
`mempool_reorg_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_reorg_test import (
    disconnected_transactions_are_available_for_relay,
    reorgs_evict_immature_and_non_final_spends,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reorgs_evict_immature_and_non_final_spends(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    reorgs_evict_immature_and_non_final_spends(bitcoind_cluster, skip_counts)


def test_disconnected_transactions_are_available_for_relay(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    disconnected_transactions_are_available_for_relay(bitcoind_cluster, skip_counts)
