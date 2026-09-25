# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_block_sync`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_block_sync.py` (`fa5f29774872`,
2025-12-16): three nodes chained `node0 -> node1 -> node2`, so that
`node1` carries both an inbound and an outbound peer, one block mined on
`node0`, and the assertion is that it reaches the other two -- Core's
own `run_test` mines and logs success, the propagation check being
`TestFramework`'s own teardown rather than a line in that file; this
rewrite makes the same check an explicit wait rather than an implicit
one, `node.wait_until_tips_agree` (`node.py`) standing in for it.

`Capability.MINE` (to mine on `node0`) and `Capability.CONNECT` (to
chain the three) are both bitcoind's unconditionally, so this is Core's
own claim in full rather than a narrowed one.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_tips_agree

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_mined_on_node0_reaches_node1_and_node2(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: mine on `node0`, and the chain of peers relays it."""
    node0, node1, node2 = bitcoind_cluster(3)
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)

    connect_nodes(node0, node1)
    connect_nodes(node1, node2)

    node0.mine(1)

    wait_until_tips_agree([node0, node1, node2])
