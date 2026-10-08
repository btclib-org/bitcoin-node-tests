# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_loadblock`, one body over either node.

Read from Core's `test/functional/feature_loadblock.py`
(`fa4fc8c1d7b5`, 2026-05-22), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node restarted with `-loadblock` (`Capability.LOAD_BLOCK`) naming a
file of the first node's chain reaches that node's height and tip.

Core writes the file with `contrib/linearize/linearize-hashes.py` and
`linearize-data.py`, scripts of its source tree the test finds through
the build's own `config.ini`; a release install is `bin/bitcoind` alone,
so this writes the file itself, in the format `linearize-data.py`
writes: for each block from the genesis block to Core's `max_height`,
in height order, the network's message start, the block's length
little-endian, and the block `getblock` serializes. That format is
`BlockDataCopier.writeBlock`'s own, which copies each record's header
from a block file as `BlockManager::WriteBlock`
(`src/node/blockstorage.cpp`) wrote it.

Core's framework connects its nodes, so its test turns the second
node's network off before the first mines. The cluster fixture
connects neither node to the other, so this asserts instead that the
second node is still at the genesis block before its restart.

Core's `restart_node` waits for the import through
`TestNode.wait_for_rpc_connection`, which polls `getmempoolinfo`'s
`loaded`; `NodeAdapter.restart` returns once RPC answers, so this polls
the same field after it.

`feature_loadblock_bitcoind_test.py` and
`feature_loadblock_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import wait_until

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["a_bootstrap_file_loads_the_chain"]

# Core's own first deterministic address, `TestNode.PRIV_KEYS`
# (`test_framework/test_node.py`), the one its `generate` pays
_ADDRESS = "mjTkW3DjgyZck4KbiRusZsqTgaYTxdSz6z"

# Core's `linearize.cfg` `max_height`, the tip its `generate` reaches
_MAX_HEIGHT = COINBASE_MATURITY


def _bootstrap(node: BitcoindAdapter | BtclibNodeAdapter) -> bytes:
    """Return `node`'s chain to `_MAX_HEIGHT`, as `linearize-data.py` writes it.

    :param node: the node whose blocks the file holds.
    """
    magic = magic_from_chain(node.chain)
    records = []
    for height in range(_MAX_HEIGHT + 1):
        block_hash = node.rpc.call("getblockhash", [height])
        raw = node.rpc.call("getblock", [block_hash, 0])
        assert isinstance(raw, str)
        block = bytes.fromhex(raw)
        records.append(magic + len(block).to_bytes(4, "little") + block)
    return b"".join(records)


def _mempool_loaded(node: BitcoindAdapter | BtclibNodeAdapter) -> bool:
    """Return `getmempoolinfo`'s own `loaded`."""
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    return info["loaded"] is True


def a_bootstrap_file_loads_the_chain(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a node given `-loadblock` reaches the tip the file holds.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param tmp_path: where the bootstrap file goes.
    :param skip_counts: the session's own tally.
    """
    source, loader = cluster(2)
    require(Capability.LOAD_BLOCK, loader.capabilities, skip_counts)
    require(Capability.GENERATE, source.capabilities, skip_counts)
    source.rpc.call("generatetoaddress", [COINBASE_MATURITY, _ADDRESS])

    bootstrap = tmp_path / "bootstrap.dat"
    bootstrap.write_bytes(_bootstrap(source))

    assert loader.rpc.call("getblockcount") == 0
    loader.restart([f"-loadblock={bootstrap}"])
    wait_until(lambda: _mempool_loaded(loader))
    assert loader.rpc.call("getblockcount") == _MAX_HEIGHT

    info = loader.rpc.call("getblockchaininfo")
    assert isinstance(info, dict)
    assert info["blocks"] == _MAX_HEIGHT
    assert source.rpc.call("getbestblockhash") == loader.rpc.call("getbestblockhash")
