# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ibd_txrelay`, rewritten on tf2's own harness: btclib-node.

`p2p_ibd_txrelay_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `TF2.md`'s per-test table carries each test's verdict.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_ibd_txrelay_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ibd_txrelay_test import (
    ibd_tx_relay_is_logged,
    ibd_tx_relay_is_withheld,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btclib_node import BtclibNodeAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_ibd_tx_relay_is_withheld(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    ibd_tx_relay_is_withheld(btclib_node_cluster, skip_counts)


def test_ibd_tx_relay_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    ibd_tx_relay_is_logged(btclib_node_cluster, skip_counts)
