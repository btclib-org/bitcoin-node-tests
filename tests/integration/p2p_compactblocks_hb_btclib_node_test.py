# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks_hb`, rewritten on tf2's own harness: btclib-node.

The same request `p2p_compactblocks_hb_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` is declared only by a build
that connects a submitted block with no peer (`btclib_node.py`'s own
docstring), and every step of this test needs a mined chain: PyPI's
`2026.9.24` is a counted skip here, and a `main` from btclib-node PR 1152
on reaches this stub's own `pytest.fail`, the scenario not being ported
yet -- either way before the other nodes it would need are started.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_compactblocks_hb_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reserved_high_bandwidth_slot_for_the_outbound_peer(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.CONNECT, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
