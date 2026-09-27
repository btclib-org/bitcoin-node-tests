# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_remove_pruned_files_on_startup`, one body over either node.

Read from Core's `test/functional/feature_remove_pruned_files_on_startup.py`
(`fa9aced8006b`, 2025-01-22), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node under `-prune=1` and `-fastprune` (`Capability.FASTPRUNE`) mines
enough blocks to fill several block files (`Capability.BLK_FILES`), and
`pruneblockchain` deletes the first two block files and their undo files
while the test holds two of them open; they stay gone once the node
restarts; and a restart with `-reindex` (`Capability.REINDEX`) wipes every
block and undo file left, the reindex from genesis writing the first of
each again. `-prune` asks for no capability, as
`rpc_getblockfrompeer_test.py`'s own docstring has.

Core's node starts at height 200, on the framework's cached chain; this
one mines to that height first, so that `pruneblockchain` is asked of a
chain as tall as Core's; none of Core's assertions depends on that height,
so none would fail without it. Every block is mined with
`generatetoaddress` (`Capability.GENERATE`) to Core's own first
deterministic address, `TestNode.PRIV_KEYS`'s own, the one Core's
`generate` pays, where Core's cached chain pays that address and three
others. The blocks are asked for `_MINE_CHUNK` at a time rather than in
Core's own batches, as `feature_reindex_init_test.py` asks for its own.

Core's own claim in full, on a platform that deletes an open file: Core
also expects a Windows host to keep the two files the test holds open,
and that branch is not ported.

The node is built over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since the test reads
and opens files inside it. The start under `-reindex` waits for
`getmempoolinfo`'s `loaded` before reading the height, as
`feature_reindex_test.py` does, whose docstring has why.

`feature_remove_pruned_files_on_startup_bitcoind_test.py` and
`feature_remove_pruned_files_on_startup_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["pruned_files_are_removed"]

# Core's own `extra_args`
_OPTIONS = ("-fastprune", "-prune=1")

# Core's own first deterministic address, `TestNode.PRIV_KEYS`
# (`test_framework/test_node.py`), the one its `generate` pays
_ADDRESS = "mjTkW3DjgyZck4KbiRusZsqTgaYTxdSz6z"

# the height Core's node starts at, on the framework's cached chain, and
# how many blocks Core's `mine_batches` mines on top
_CACHE_HEIGHT = 200
_BLOCKS = 800

# how many blocks one `generatetoaddress` call asks for: it answers only
# once every block is mined, and has to inside the RPC client's own
# timeout (`timeout_factor.rpc_client_timeout`)
_MINE_CHUNK = 50

# the height Core's `pruneblockchain` call prunes up to, and how many
# block and undo files Core expects left once the node restarts
_PRUNE_HEIGHT = 600
_FILES_LEFT = 4


def _block_and_undo_files(blocks: Path) -> list[str]:
    """Return the names of `blocks`'s own `blk*` and `rev*` files, sorted.

    Core's own `ls_files`.
    """
    return sorted(
        entry.name
        for entry in blocks.iterdir()
        if entry.is_file() and entry.name.startswith(("blk", "rev"))
    )


def _mempool_loaded(node: BitcoindAdapter | BtclibNodeAdapter) -> bool:
    """Return `getmempoolinfo`'s own `loaded`."""
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    return info["loaded"] is True


def pruned_files_are_removed(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check pruned block files go, open or not, and `-reindex` wipes the rest.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, datadir, rpc_port, p2p_port, _OPTIONS)
    for capability in (
        Capability.FASTPRUNE,
        Capability.GENERATE,
        Capability.BLK_FILES,
        Capability.REINDEX,
    ):
        require(capability, node.capabilities, skip_counts)
    blocks = datadir / "regtest" / "blocks"
    blk0 = blocks / "blk00000.dat"
    rev0 = blocks / "rev00000.dat"
    blk1 = blocks / "blk00001.dat"
    rev1 = blocks / "rev00001.dat"
    pruned = (blk0, rev0, blk1, rev1)
    try:
        node.start()
        for _ in range((_CACHE_HEIGHT + _BLOCKS) // _MINE_CHUNK):
            node.rpc.call("generatetoaddress", [_MINE_CHUNK, _ADDRESS])

        with blk0.open("rb"), rev1.open("rb"):
            node.rpc.call("pruneblockchain", [_PRUNE_HEIGHT])
            assert not any(path.exists() for path in pruned)

        node.restart()
        assert not blk0.exists()
        assert not rev1.exists()

        assert len(_block_and_undo_files(blocks)) == _FILES_LEFT
        node.restart([*_OPTIONS, "-reindex"])
        wait_until(lambda: _mempool_loaded(node))
        assert node.rpc.call("getblockcount") == 0
        node.stop()
        assert _block_and_undo_files(blocks) == ["blk00000.dat", "rev00000.dat"]
    finally:
        node.stop()
