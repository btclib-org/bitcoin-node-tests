# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak_tx`, on tf2's own harness: btclib-node.

`p2p_leak_tx_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
Each body asks for `Capability.CLOCK` first and then for `Capability.MINE`.
`TF2.md`'s per-test table carries each test's verdict.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_leak_tx_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_leak_tx_test import (
    notfound_on_replaced_tx,
    notfound_on_unannounced_tx,
    tx_in_block,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_tx_in_block(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    tx_in_block(btclib_node_cluster, skip_counts)


def test_notfound_on_replaced_tx(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    notfound_on_replaced_tx(btclib_node_cluster, skip_counts)


def test_notfound_on_unannounced_tx(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    notfound_on_unannounced_tx(btclib_node_cluster, skip_counts)
