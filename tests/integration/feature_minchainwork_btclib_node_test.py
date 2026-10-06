# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_minchainwork`, rewritten on tf2's own harness: btclib-node.

`feature_minchainwork_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on
`Capability.MINIMUM_CHAIN_WORK`, which `btclib_node.py`'s own docstring
has no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_minchainwork_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_minchainwork_test import (
    block_relay_waits_for_the_minimum_chain_work,
    outbound_peers_with_too_little_work_are_dropped_in_ibd,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_block_relay_waits_for_the_minimum_chain_work(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    block_relay_waits_for_the_minimum_chain_work(btclib_node_cluster, skip_counts)


def test_outbound_peers_with_too_little_work_are_dropped_in_ibd(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    outbound_peers_with_too_little_work_are_dropped_in_ibd(
        btclib_node_cluster, skip_counts
    )
