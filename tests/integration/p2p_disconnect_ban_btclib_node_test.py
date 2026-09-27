# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_disconnect_ban`, its `disconnectnode` half: btclib-node.

The same requests `p2p_disconnect_ban_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DISCONNECT` is not declared on any
build (`btclib_node.py`'s own docstring), so the test skips before a
second node or a `disconnectnode` call is ever made; on a build
declaring it, the test reaches its own `pytest.fail`, no scenario being
ported for this node.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_disconnect_ban_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_disconnectnode_drops_a_peer_by_address_and_by_node_id(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The target: the requests `p2p_disconnect_ban_bitcoind_test.py` makes."""
    require(Capability.CONNECT, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.DISCONNECT, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
