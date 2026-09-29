# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_startupnotify`, one body over either node.

Read from Core's `test/functional/feature_startupnotify.py`
(`fa71c15f8610`, 2025-11-26), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node started without `-startupnotify` writes no file, and restarted
with it (`Capability.STARTUP_NOTIFY`) runs the command once, which
appends a line to a file inside its data directory, and answers RPC.

Core's command names the file relative to the directory its harness
starts each node in, the parent of the node's data directory; this
harness starts a node in its caller's own directory, so the command
names the file by its absolute path instead.

Core's node starts at height 200, on the framework's cached chain, and
Core's last check reads that height back; this node starts on a fresh
chain, so the same check reads `0`.

The node is built over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since the test reads a
file the command writes inside it.

`feature_startupnotify_bitcoind_test.py` and
`feature_startupnotify_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import shlex
from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["the_startup_command_runs_once"]

# Core's own `FILE_NAME`, the file the command appends to and the line
# it appends
_FILE_NAME = "test.txt"


def _count(notified: Path) -> int:
    """Return how many times `notified` holds `_FILE_NAME`.

    Core's own `get_count`.
    """
    return notified.read_text(encoding="utf-8").count(_FILE_NAME)


def the_startup_command_runs_once(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-startupnotify`'s command runs once, on a start given it alone.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    require(Capability.STARTUP_NOTIFY, node.capabilities, skip_counts)
    notified = datadir / _FILE_NAME
    command = f"echo '{_FILE_NAME}' >> {shlex.quote(str(notified))}"
    try:
        node.start()
        assert not notified.exists()

        node.restart([f"-startupnotify={command}"])
        wait_until(notified.exists)

        wait_until(lambda: _count(notified) > 0)
        assert _count(notified) == 1

        assert node.rpc.call("getblockcount") == 0
    finally:
        node.stop()
