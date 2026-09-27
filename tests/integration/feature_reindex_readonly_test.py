# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex_readonly`, one body over either node.

Read from Core's `test/functional/feature_reindex_readonly.py`
(`6eca11175be6`, 2026-07-16), the option, disk and log families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node under `-fastprune` (`Capability.FASTPRUNE`) mines a block larger
than a block file, so its chain spills into the next block file, and,
restarted with `-reindex` (`Capability.REINDEX`) once the first of them
is read-only, reindexes from every block file, logging "Reindexing
finished", and comes back at the height it had. The block is Core's
own: `generateblock` (`Capability.GENERATE`) paying an `OP_RETURN`
output past a block file's size, with no transaction. The block files
are Core's own layout (`Capability.BLK_FILES`).

Core makes the file read-only with its mode, then also tries the
immutable flag -- `chattr +i` on Linux, `chflags uchg` on macOS and the
BSDs -- and returns without reindexing where that fails under root. The
flag is what keeps root from writing to the file, root being exempt
from a file's mode and every other user not. This takes the mode alone
and asserts the file is unwritable to this process -- the node runs as
the same user -- before the node restarts, so a run under root fails on
that assertion rather than reindexing a file it could write to. The
flag and its undo are not ported.

The node is built over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since the test changes
a file inside it. The wait after the restart is
`feature_reindex_test.py`'s own.

`feature_reindex_readonly_bitcoind_test.py` and
`feature_reindex_readonly_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import free_ports, wait_until

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["a_read_only_block_file_is_reindexed"]

# Core's own `fastprune_blockfile_size`, and the output its block pays:
# `OP_RETURN` followed by that many `0xff` octets
_FASTPRUNE_BLOCKFILE_SIZE = 0x10000
_OUTPUT = f"raw(6a{'ff' * _FASTPRUNE_BLOCKFILE_SIZE})"

# Core's own `assert_debug_log` timeout for the reindex
_REINDEX_TIMEOUT = 60

# `ImportBlocks`'s own (`src/node/blockstorage.cpp`)
_REINDEX_FINISHED = "Reindexing finished"


def _mempool_loaded(node: BitcoindAdapter) -> bool:
    """Return `getmempoolinfo`'s own `loaded`."""
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    return info["loaded"] is True


def a_read_only_block_file_is_reindexed(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a reindex reads a block file it cannot write to.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    :raises TypeError: the node declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    for capability in (
        Capability.REINDEX,
        Capability.FASTPRUNE,
        Capability.GENERATE,
        Capability.BLK_FILES,
        Capability.DEBUG_LOG,
    ):
        require(capability, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    blocks = datadir / "regtest" / "blocks"
    first = blocks / "blk00000.dat"
    try:
        node.restart(["-fastprune"])
        node.rpc.call("generateblock", [_OUTPUT, []])
        height = node.rpc.call("getblockcount")
        node.stop()

        assert first.exists()
        assert (blocks / "blk00001.dat").exists()
        first.chmod(stat.S_IREAD)
        assert not os.access(first, os.W_OK)

        with assert_debug_log(
            node.debug_log_path, [_REINDEX_FINISHED], timeout=_REINDEX_TIMEOUT
        ):
            node.restart(["-reindex", "-fastprune"])
            wait_until(lambda: _mempool_loaded(node))
        assert node.rpc.call("getblockcount") == height
    finally:
        node.stop()
        if first.exists():
            first.chmod(stat.S_IREAD | stat.S_IWRITE)
