# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_node_network_limited`, on tf2's own harness: btclib-node.

`p2p_node_network_limited_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` and `Capability.DISCONNECT` are
declared per build, and `Capability.SUSPEND_NETWORK` by none
(`btclib_node.py`'s own docstring), so this is a counted skip before any
node is restarted or mined on.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_node_network_limited_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_node_network_limited_test import node_network_limited

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_node_network_limited(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    node_network_limited(btclib_node_cluster, skip_counts)
