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

The refusal is Core's own wording alone, `Cannot obtain a lock on
directory <path>. `, naming the directory locked, the way
`feature_filelock_bitcoind_test.py` matches it. btclib-node writes it
past [ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147),
locking the data directory and then the blocks directory before either
store opens. The released `2026.9.24` fails both tests: its RocksDB
stores fail uncaught, with `Exception: IO error: While lock file:
<path>/LOCK: Resource temporarily unavailable`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_filelock_btclib_node_test.py
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def _lock_refusal(directory: Path) -> str:
    """Core's own refusal for `directory`, which each test pins.

    The pattern `feature_filelock_bitcoind_test.py` matches bitcoind
    against: the locked path is compared, so that a datadir refusal
    cannot stand in for a blocksdir one or the reverse, and the client
    name is the build's.
    """
    return (
        re.escape(f"Cannot obtain a lock on directory {directory}. ")
        + r".* is probably already running\."
    )


def test_second_instance_on_same_datadir_refuses_to_start(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node over the same datadir cannot obtain its lock."""
    datadir = tmp_path / "datadir"
    rpc_port1, p2p_port1 = free_ports(2)
    first = make_adapter(
        BtclibNodeAdapter, btclib_node_python, datadir, rpc_port1, p2p_port1
    )
    first.start()
    try:
        rpc_port2, p2p_port2 = free_ports(2)
        second = make_adapter(
            BtclibNodeAdapter, btclib_node_python, datadir, rpc_port2, p2p_port2
        )
        with pytest.raises(RuntimeError, match=_lock_refusal(datadir / "regtest")):
            second.start()
    finally:
        first.stop()


def test_second_instance_on_same_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node given the first's own datadir as `-blocksdir` fails."""
    first_datadir = tmp_path / "first"
    rpc_port1, p2p_port1 = free_ports(2)
    first = make_adapter(
        BtclibNodeAdapter, btclib_node_python, first_datadir, rpc_port1, p2p_port1
    )
    first.start()
    try:
        rpc_port2, p2p_port2 = free_ports(2)
        second = make_adapter(
            BtclibNodeAdapter,
            btclib_node_python,
            tmp_path / "second",
            rpc_port2,
            p2p_port2,
            extra_args=(f"-blocksdir={first_datadir}",),
        )
        with pytest.raises(
            RuntimeError, match=_lock_refusal(first_datadir / "regtest" / "blocks")
        ):
            second.start()
    finally:
        first.stop()
