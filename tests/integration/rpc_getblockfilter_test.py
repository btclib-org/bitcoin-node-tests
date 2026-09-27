# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockfilter`, one body over either node.

Read from Core's `test/functional/rpc_getblockfilter.py` (`fa5f29774872`,
2025-12-16): two nodes, the first under `-blockfilterindex`
(`Capability.BLOCK_FILTER_INDEX`), each mining its own chain apart
(`Capability.MINE`), then connected (`Capability.CONNECT`) so that the
first reorgs onto the second's longer chain. `getblockfilter` answers a
hex filter for every block of the active chain and of the stale one,
refuses an unknown block and an unknown filter type, and, restarted
with `-blockfilterindex=0`, refuses every filter type as not enabled.

Core's own claim in full. Core's harness connects its nodes at setup
and its test disconnects them first; this harness's nodes start
unconnected, so there is nothing to disconnect.
`rpc_getblockfilter_bitcoind_test.py` and
`rpc_getblockfilter_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_tips_agree

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["getblockfilter_answers_for_active_and_stale_blocks"]

# Core's own `FILTER_TYPES`
_FILTER_TYPES = ("basic",)


def _hashes(node: NodeAdapter, heights: range) -> list[str]:
    return [node.rpc.call("getblockhash", [height]) for height in heights]


def getblockfilter_answers_for_active_and_stale_blocks(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.BLOCK_FILTER_INDEX, node0.capabilities, skip_counts)
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.MINE, node1.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    node0.restart(["-blockfilterindex"])

    # two chains, mined apart
    node0.mine(3)
    node1.mine(4)
    assert node0.rpc.call("getblockcount") == 3
    chain0_hashes = _hashes(node0, range(4))

    # node 0 reorgs onto node 1's longer chain
    connect_nodes(node0, node1)
    wait_until_tips_agree([node0, node1])
    assert node0.rpc.call("getblockcount") == 4
    chain1_hashes = _hashes(node0, range(4))

    # a filter for every block, on the active chain and on the stale one
    for block_hash in [*chain1_hashes, *chain0_hashes]:
        for filter_type in _FILTER_TYPES:
            result = node0.rpc.call("getblockfilter", [block_hash, filter_type])
            assert bytes.fromhex(result["filter"])

    bad_block_hash = "0123456789abcdef" * 4
    with pytest.raises(RpcError, match="Block not found") as excinfo:
        node0.rpc.call("getblockfilter", [bad_block_hash, "basic"])
    assert excinfo.value.code == -5

    genesis_hash = node0.rpc.call("getblockhash", [0])
    with pytest.raises(RpcError, match="Unknown filtertype") as excinfo:
        node0.rpc.call("getblockfilter", [genesis_hash, "unknown"])
    assert excinfo.value.code == -5

    # without the index, every filter type is refused as not enabled
    node0.restart(["-blockfilterindex=0"])
    for filter_type in _FILTER_TYPES:
        with pytest.raises(
            RpcError, match=f"Index is not enabled for filtertype {filter_type}"
        ) as excinfo:
            node0.rpc.call("getblockfilter", [genesis_hash, filter_type])
        assert excinfo.value.code == -1
