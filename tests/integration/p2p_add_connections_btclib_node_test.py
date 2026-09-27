# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_add_connections`, rewritten on tf2's own harness: btclib-node.

`p2p_add_connections_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TYPED_OUTBOUND` is declared by no
build (`btclib_node.py`'s own docstring), so each test is a counted skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_add_connections_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_add_connections_test import (
    manual_connection_past_the_outbound_capacity,
    outbound_connections_by_type,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_manual_connection_past_the_outbound_capacity(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    manual_connection_past_the_outbound_capacity(btclib_node_cluster, skip_counts)


def test_outbound_connections_by_type(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    outbound_connections_by_type(btclib_node_cluster, skip_counts)
