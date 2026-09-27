# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ping`, rewritten on this harness: btclib-node.

`p2p_ping_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
Both tests are a counted skip on `Capability.PEER_TIMEOUT`, which
`btclib_node.py`'s own docstring has no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_ping_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ping_test import (
    ping_replies_are_logged,
    ping_replies_are_reported_on_rpc,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_ping_replies_are_reported_on_rpc(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    ping_replies_are_reported_on_rpc(btclib_node_cluster, skip_counts)


def test_ping_replies_are_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    ping_replies_are_logged(btclib_node_cluster, skip_counts)
