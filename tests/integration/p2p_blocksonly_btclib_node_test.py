# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_blocksonly`, rewritten on tf2's own harness: btclib-node.

`p2p_blocksonly_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_blocksonly_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_blocksonly_test import (
    a_block_relay_only_peer_is_refused_transactions,
    a_block_relay_only_peer_refusal_is_logged,
    a_blocksonly_node_refusal_is_logged,
    a_blocksonly_node_refuses_transactions,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_relay_only_peer_is_refused_transactions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_block_relay_only_peer_is_refused_transactions(btclib_node_cluster, skip_counts)


def test_a_block_relay_only_peer_refusal_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_block_relay_only_peer_refusal_is_logged(btclib_node_cluster, skip_counts)


def test_a_blocksonly_node_refuses_transactions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_blocksonly_node_refuses_transactions(btclib_node_cluster, skip_counts)


def test_a_blocksonly_node_refusal_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_blocksonly_node_refusal_is_logged(btclib_node_cluster, skip_counts)
