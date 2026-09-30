# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_reorg`, rewritten on tf2's own harness: btclib-node.

`mempool_reorg_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on every build: on
PyPI's `2026.9.24`, which declares no `Capability.MINE`, and on a `main`
past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
on `Capability.INVALIDATE_BLOCK` and on `Capability.CLOCK` respectively,
which no build declares (`btclib_node.py`'s own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_reorg_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reorgs_evict_immature_and_non_final_spends(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    reorgs_evict_immature_and_non_final_spends(btclib_node_cluster, skip_counts)


def test_disconnected_transactions_are_available_for_relay(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    disconnected_transactions_are_available_for_relay(btclib_node_cluster, skip_counts)
