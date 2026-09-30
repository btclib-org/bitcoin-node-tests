# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_disconnect_ban`, its `disconnectnode` half: btclib-node.

`p2p_disconnect_ban_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DISCONNECT` is declared only by a
build naming `disconnectnode` (`btclib_node.py`'s own docstring): PyPI's
`2026.9.24` skips once its two nodes are started, before a
`disconnectnode` call is made.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_disconnect_ban_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_disconnect_ban_test import (
    disconnectnode_drops_a_peer_by_address_and_by_node_id,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_disconnectnode_drops_a_peer_by_address_and_by_node_id(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    disconnectnode_drops_a_peer_by_address_and_by_node_id(
        btclib_node_cluster, skip_counts
    )
