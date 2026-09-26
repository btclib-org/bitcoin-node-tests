# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: bitcoind.

What `tests/node_test.py` and `tests/bitcoind_test.py` fake, run against
the process itself: `mine` after a `restart` and over a datadir an
earlier adapter left
([ISS 86](https://github.com/btclib-org/bitcoin-node-tests/issues/86)),
and `stop` reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import os
import signal
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def _adapter(
    bitcoind_path: str, datadir: Path, skip_counts: SkipCounts
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(bitcoind_path, datadir, rpc_port, p2p_port)
    require(Capability.MINE, adapter.capabilities, skip_counts)
    return adapter


def test_mine_after_restart(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A restart unloads the wallet `mine` pays to; `mine` loads it back."""
    adapter = _adapter(bitcoind_path, tmp_path / "node", skip_counts)
    adapter.start()
    try:
        adapter.mine(1)
        adapter.restart()
        adapter.mine(1)
        assert adapter.rpc.call("getblockcount") == 2
    finally:
        adapter.stop()


def test_mine_over_a_datadir_an_earlier_adapter_left(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A second adapter over the same datadir mines to the wallet on disk."""
    datadir = tmp_path / "node"
    first = _adapter(bitcoind_path, datadir, skip_counts)
    first.start()
    try:
        first.mine(1)
    finally:
        first.stop()
    second = _adapter(bitcoind_path, datadir, skip_counts)
    second.start()
    try:
        second.mine(1)
        assert second.rpc.call("getblockcount") == 2
    finally:
        second.stop()


def test_stop_reports_a_node_killed_out_from_under_it(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """A node gone before `stop` is raised, and nothing is left to stop."""
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(bitcoind_path, tmp_path / "node", rpc_port, p2p_port)
    adapter.start()
    process = adapter._process
    assert process is not None
    os.kill(process.pid, signal.SIGKILL)
    process.wait()
    with pytest.raises(
        RuntimeError, match=r"^node process exited with -9 before stop was called"
    ):
        adapter.stop()
    adapter.stop()
