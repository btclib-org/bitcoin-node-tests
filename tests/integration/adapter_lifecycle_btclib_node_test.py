# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: btclib-node.

`stop` reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)),
the half of `adapter_lifecycle_bitcoind_test.py` that is `node.py`'s
rather than `BitcoindAdapter.mine`'s; and `BtclibNodeAdapter.mine`
against the process itself, which `tests/btclib_node_test.py` fakes
([ISS 56](https://github.com/btclib-org/bitcoin-node-tests/issues/56)),
a counted skip on `Capability.MINE` for a build that does not declare it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/adapter_lifecycle_btclib_node_test.py
"""

from __future__ import annotations

import os
import signal
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_stop_reports_a_node_killed_out_from_under_it(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """A node gone before `stop` is raised, and nothing is left to stop."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, tmp_path / "node", rpc_port, p2p_port
    )
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


def test_mine_extends_the_tip_by_the_blocks_it_returns(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Each `mine` moves the tip onto the last hash, oldest first."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, tmp_path / "node", rpc_port, p2p_port
    )
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
