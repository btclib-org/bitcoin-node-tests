# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex_init`, one body over either node.

Read from Core's `test/functional/feature_reindex_init.py`
(`0d1301b47a35`, 2026-03-24), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node stopped and its block index removed from `blocks/index` refuses
to start, advising a reindex in Core's own words, and started again
with `-test=reindex_after_failure_noninteractive_yes`
(`Capability.REINDEX_AFTER_FAILURE`) reindexes from its block files
back to the height it had. `blocks/` is Core's own layout
(`Capability.BLK_FILES`), under the regtest chain's own directory, the
chain every node of this suite starts on by default.

Core's own claim in full. Its chain is the framework's cached one; this
node mines its own to the same height (`Capability.MINE`). The node is
built over a data directory of its own, through `make_adapter`
(`tests/integration/conftest.py`), since the test removes a directory
inside it. Core's harness waits, after a start, for `getmempoolinfo`'s
`loaded`, "for the node to finish reindex, block import, and loading the
mempool" (`TestNode.wait_for_rpc_connection`'s own comment), where
`NodeAdapter.start` returns on the first RPC answer. This waits the same
way before reading the height: without the wait, `getblockcount` answered
`0` right after the start, measured against the pinned release.

`feature_reindex_init_bitcoind_test.py` and
`feature_reindex_init_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import os
import re
import shutil
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["a_lost_block_index_is_rebuilt_once_allowed"]

# the height of Core's own cached chain
_HEIGHT = 200

# how many blocks one `mine` call asks for, as `rpc_getblockfrompeer_test`
# chunks them: a bitcoind's own `generatetoaddress` answers only once every
# block is mined, and the whole height in one call outlasted the RPC
# client's own timeout on the pinned release, measured on a loaded machine
_MINE_CHUNK = 50

# Core's own `expected_msg`
_NO_BLOCK_INDEX = (
    f"Error initializing block database.{os.linesep}"
    "Please restart with -reindex or -reindex-chainstate to recover."
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)


def _mempool_loaded(node: BitcoindAdapter | BtclibNodeAdapter) -> bool:
    """Return `getmempoolinfo`'s own `loaded`."""
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    return info["loaded"] is True


def a_lost_block_index_is_rebuilt_once_allowed(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a start refuses a lost block index, and one allowed reindexes.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    require(Capability.REINDEX_AFTER_FAILURE, node.capabilities, skip_counts)
    require(Capability.BLK_FILES, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    try:
        node.start()
        for _ in range(_HEIGHT // _MINE_CHUNK):
            node.mine(_MINE_CHUNK)
        node.stop()

        shutil.rmtree(datadir / "regtest" / "blocks" / "index")
        with pytest.raises(RuntimeError) as refused:
            node.start()
        early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
        assert early_exit is not None
        assert int(early_exit[1]) != 0
        assert early_exit[2].strip() == _NO_BLOCK_INDEX

        node.restart(["-test=reindex_after_failure_noninteractive_yes"])
        wait_until(lambda: _mempool_loaded(node))
        assert node.rpc.call("getblockcount") == _HEIGHT
    finally:
        node.stop()
