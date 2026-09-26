# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: btclib-node.

`stop` reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)),
the half of `adapter_lifecycle_bitcoind_test.py` that is `node.py`'s
rather than `BitcoindAdapter.mine`'s.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/adapter_lifecycle_btclib_node_test.py
"""

from __future__ import annotations

import os
import signal
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


def test_stop_reports_a_node_killed_out_from_under_it(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """A node gone before `stop` is raised, and nothing is left to stop."""
    rpc_port, p2p_port = free_ports(2)
    adapter = BtclibNodeAdapter(
        btclib_node_python, tmp_path / "node", rpc_port, p2p_port
    )
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
