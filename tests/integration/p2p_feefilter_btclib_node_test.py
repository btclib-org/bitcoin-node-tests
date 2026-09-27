# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_feefilter`, rewritten on tf2's own harness: btclib-node.

`p2p_feefilter_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_feefilter_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_feefilter_test import (
    feefilter_filters_announcements,
    feefilter_is_not_sent_in_blocks_only_mode,
    feefilter_is_not_sent_to_a_block_relay_only_peer,
    feefilter_is_not_sent_to_a_forcerelay_peer,
    feefilter_is_sent_to_an_inbound_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_feefilter_is_sent_to_an_inbound_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    feefilter_is_sent_to_an_inbound_peer(btclib_node_cluster)


def test_feefilter_is_not_sent_to_a_forcerelay_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    feefilter_is_not_sent_to_a_forcerelay_peer(btclib_node_cluster)


def test_feefilter_filters_announcements(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    feefilter_filters_announcements(btclib_node_cluster, skip_counts)


def test_feefilter_is_not_sent_to_a_block_relay_only_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    feefilter_is_not_sent_to_a_block_relay_only_peer(btclib_node_cluster, skip_counts)


def test_feefilter_is_not_sent_in_blocks_only_mode(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    feefilter_is_not_sent_in_blocks_only_mode(btclib_node_cluster, skip_counts)
