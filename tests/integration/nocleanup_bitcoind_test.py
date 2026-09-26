# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--nocleanup`, measured as already true: bitcoind.

Issue [bitcoin-node-tests#36](https://github.com/btclib-org/bitcoin-node-tests/issues/36):
`NodeAdapter.stop` (`node.py`) only terminates the process, never
removing the data directory it wrote to -- there is nothing here for a
`--nocleanup` flag to disable. CONTRIBUTING.md's own *Running against a
Core developer's own build* has the other half, that pytest's own
`tmp_path`/`--basetemp` do not delete a run's own directories either
when the run ends.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


def test_stop_leaves_the_datadir_and_its_debug_log_on_disk(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """The datadir, and the log inside it, both outlive `stop`."""
    datadir = tmp_path / "node"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(bitcoind_path, datadir, rpc_port, p2p_port)
    adapter.start()
    log_path = adapter.debug_log_path
    try:
        assert log_path.exists()
    finally:
        adapter.stop()
    assert datadir.exists()
    assert log_path.exists()
