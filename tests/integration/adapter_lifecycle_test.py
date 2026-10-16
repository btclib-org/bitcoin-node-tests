# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle, one body over each node.

What `tests/node_test.py` and `tests/bitcoind_test.py` fake, run
against the process itself: `stop`
reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)),
and `mine` extending the tip by the blocks it returns
([ISS 56](https://github.com/btclib-org/bitcoin-node-tests/issues/56)),
a counted skip on `Capability.MINE` for a build that does not declare it.

Each `adapter_lifecycle_<node>_test.py` module beside this one runs it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import os
import signal
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "mine_extends_the_tip_by_the_blocks_it_returns",
    "stop_reports_a_node_killed_out_from_under_it",
]


def stop_reports_a_node_killed_out_from_under_it(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check a node gone before `stop` is raised, and nothing is left to stop.

    :param make_adapter: the session's own adapter factory.
    :param cls: the node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(cls, executable, tmp_path / "node", rpc_port, p2p_port)
    adapter.start()
    running = adapter._running
    process = None if running is None else running.process
    try:
        assert process is not None
        os.kill(process.pid, signal.SIGKILL)
        process.wait()
        with pytest.raises(
            RuntimeError, match=r"^node process exited with -9 before stop was called"
        ):
            adapter.stop()
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
    adapter.stop()


def mine_extends_the_tip_by_the_blocks_it_returns(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check each `mine` moves the tip onto the last hash, oldest first.

    :param make_adapter: the session's own adapter factory.
    :param cls: the node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(cls, executable, tmp_path / "node", rpc_port, p2p_port)
    require(Capability.MINE, adapter.capabilities, skip_counts)
    adapter.start()
    try:
        start = adapter.rpc.call("getblockcount")
        assert isinstance(start, int)
        (first,) = adapter.mine(1)
        assert adapter.rpc.call("getblockcount") == start + 1
        assert adapter.rpc.call("getbestblockhash") == first
        batch = adapter.mine(3)
        assert len(batch) == len(set(batch)) == 3
        assert adapter.rpc.call("getblockcount") == start + 4
        assert adapter.rpc.call("getbestblockhash") == batch[-1]
        heights = [
            adapter.rpc.call("getblockheader", [block_hash])["height"]
            for block_hash in batch
        ]
        assert heights == [start + 2, start + 3, start + 4]
    finally:
        adapter.stop()
