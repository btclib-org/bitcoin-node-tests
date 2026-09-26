# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""A block mined on bitcoind reaches btclib-node, over a real connection.

[ISS 43](https://github.com/btclib-org/bitcoin-node-tests/issues/43)'s
own "most valuable case": bitcoind mines, and btclib-node -- never
asked to mine anything itself -- receives the block from a real peer
rather than from `submitblock` on its own behalf. `Capability.MINE` is
never declared by `BtclibNodeAdapter` (`btclib_node.py`'s own
docstring), but nothing here asks it for that; `Capability.CONNECT` is
declared by both (`bitcoind.py`, `btclib_node.py`), which is the whole
of what this needs.

Not a port of any Core file, unlike every other module of
`tests/integration/`: Core's own functional tests run one binary
against copies of itself, so no Core test poses this question the way
`TF2.md`'s own per-test ledger expects one pinned. `TF2.md` carries this
result in its own prose instead, under its own heading, rather than as
a per-test row. The module is named `*_btclib_node_test.py` because it
needs a btclib-node: `node-integration.yml`'s btclib-node jobs run those
modules, and its required bitcoind job, which has none, exempts them.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mixed_cluster_block_sync_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_tips_agree

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_mined_on_bitcoind_reaches_btclib_node(
    mixed_cluster: tuple[BitcoindAdapter, BtclibNodeAdapter],
    skip_counts: SkipCounts,
) -> None:
    """Bitcoind mines; btclib-node connects, and its own tip catches up."""
    bitcoind, btclib_node = mixed_cluster
    require(Capability.MINE, bitcoind.capabilities, skip_counts)
    require(Capability.CONNECT, bitcoind.capabilities, skip_counts)
    require(Capability.CONNECT, btclib_node.capabilities, skip_counts)

    connect_nodes(bitcoind, btclib_node)
    bitcoind.mine(1)

    wait_until_tips_agree([bitcoind, btclib_node])
