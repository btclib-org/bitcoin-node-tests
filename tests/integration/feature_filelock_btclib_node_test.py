# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, rewritten on this harness: btclib-node.

The same claim `feature_filelock_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
a second process over the same datadir or blocksdir refuses to start.
No `Capability` is asked for -- the refusal is a process fact every
`NodeAdapter` already answers (`node.py`'s own `start`), not one either
node declares or withholds.

Two wordings are live across the builds this suite runs against, both
this node's own rather than bitcoind's, and the match below accepts
either rather than picking one -- the smaller design against a version
switch, since nothing here needs to know which build is running, only
that its own refusal names the directory it could not lock. The
released build (PyPI, `2026.9.24` and every build before
[ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147)
landed) leaves each database's own `Rdict` (RocksDB) to fail uncaught:
measured live, a second `python -m btclib_node` pointed at a datadir (or
a blocksdir) already open exits 1 with `Exception: IO error: While lock
file: <path>/LOCK: Resource temporarily unavailable`, naming the
`chainstate` or the `blocks` subdirectory RocksDB itself opened. A build
past #1147's fix (`main`) locks the data directory and then the blocks
directory before either store opens, and answers the same conflict with
Core's own clean init error, "Error: Cannot obtain a lock on directory
<path>. btclib-node is probably already running.", naming the directory
`Node.__init__` locked rather than a RocksDB-internal path -- measured
live against a `main` build, `<datadir>/regtest` for the first test
below and `<first datadir>/regtest/blocks` for the second, matching
`feature_filelock_bitcoind_test.py`'s own wording once every build in
this suite's own matrix is past the fix.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_filelock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration

# The released build's own uncaught RocksDB wording, naming the
# subdirectory its `Rdict` opened, alternated with the fixed build's own
# clean refusal, naming the directory `Node.__init__` locked instead --
# see the module docstring for which build emits which. Each alternative
# pins its own directory, so neither test accepts the other's refusal.
_DATADIR_LOCK_REFUSAL = (
    r"chainstate[/\\]LOCK"
    r"|Cannot obtain a lock on directory \S*[/\\]regtest\. "
)
_BLOCKSDIR_LOCK_REFUSAL = (
    r"blocks[/\\]LOCK"
    r"|Cannot obtain a lock on directory \S*[/\\]regtest[/\\]blocks\. "
)


def test_second_instance_on_same_datadir_refuses_to_start(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node over the same datadir cannot lock its own chainstate."""
    datadir = tmp_path / "datadir"
    rpc_port1, p2p_port1 = free_ports(2)
    first = BtclibNodeAdapter(btclib_node_python, datadir, rpc_port1, p2p_port1)
    first.start()
    try:
        rpc_port2, p2p_port2 = free_ports(2)
        second = BtclibNodeAdapter(btclib_node_python, datadir, rpc_port2, p2p_port2)
        with pytest.raises(RuntimeError, match=_DATADIR_LOCK_REFUSAL):
            second.start()
    finally:
        first.stop()


def test_second_instance_on_same_blocksdir_refuses_to_start(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node given the first's own datadir as `-blocksdir` fails."""
    first_datadir = tmp_path / "first"
    rpc_port1, p2p_port1 = free_ports(2)
    first = BtclibNodeAdapter(btclib_node_python, first_datadir, rpc_port1, p2p_port1)
    first.start()
    try:
        rpc_port2, p2p_port2 = free_ports(2)
        second = BtclibNodeAdapter(
            btclib_node_python,
            tmp_path / "second",
            rpc_port2,
            p2p_port2,
            extra_args=(f"-blocksdir={first_datadir}",),
        )
        with pytest.raises(RuntimeError, match=_BLOCKSDIR_LOCK_REFUSAL):
            second.start()
    finally:
        first.stop()
