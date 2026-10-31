# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, one body over each node.

Read from Core's `test/functional/feature_filelock.py` (`fa5f29774872`,
2025-12-16): a second process started over a datadir, or a blocksdir, a
first one already holds is fatal, disk-family mechanism alone
(issue btclib-org/btclib#2220,
[ISS 7](https://github.com/btclib-org/btclib-functional-tests/issues/7)) --
`NodeAdapter.start`'s own capture of a process's early exit (`node.py`)
is what every `assert_start_raises_init_error`-shaped test already
reads through. The datadir's refusal asks for no `Capability`: it is a
process fact every `NodeAdapter` answers. The blocksdir's asks for
`Capability.BLOCKS_DIR`, the option it gives the second node.

A smaller claim than Core's own file, declared rather than silent: the
cookie- and PID-file persistence checks and the wallet-directory lock
are dropped. The first two are a fact about which files a node
happens to leave behind after a refused second start, not about the
lock itself; the third is a wallet fact, out of this suite's reach by
the charter's own rule.

The refusal is Core's own wording, `Cannot obtain a lock on directory
<path>. `, naming the directory locked.

Each `feature_filelock_<node>_test.py` module beside this one runs it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.capability import Capability, require
from btclib_functional_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from btclib_functional_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "second_instance_on_same_blocksdir_refuses_to_start",
    "second_instance_on_same_datadir_refuses_to_start",
]


def _lock_refusal(directory: Path) -> str:
    """Core's own refusal for `directory`, which each test pins.

    Core's file compares the whole message, the locked path included, so
    that a datadir refusal cannot stand in for a blocksdir one or the
    reverse; the client name between the path and the closing clause is
    the build's, and is left to the pattern.
    """
    return (
        re.escape(f"Cannot obtain a lock on directory {directory}. ")
        + r".* is probably already running\."
    )


def second_instance_on_same_datadir_refuses_to_start(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check a second node over the same datadir cannot obtain its lock.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    rpc_port1, p2p_port1 = free_ports(2)
    first = make_adapter(cls, executable, datadir, rpc_port1, p2p_port1)
    first.start()
    rpc_port2, p2p_port2 = free_ports(2)
    second = make_adapter(cls, executable, datadir, rpc_port2, p2p_port2)
    try:
        with pytest.raises(RuntimeError, match=_lock_refusal(datadir / "regtest")):
            second.start()
    finally:
        second.stop()
        first.stop()


def second_instance_on_same_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a second node given the first's own datadir as `-blocksdir` fails.

    The capability is asked of a node built without the option: a node
    that reads `-blocksdir` as another option refuses the construction.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    first_datadir = tmp_path / "first"
    rpc_port1, p2p_port1 = free_ports(2)
    first = make_adapter(cls, executable, first_datadir, rpc_port1, p2p_port1)
    require(Capability.BLOCKS_DIR, first.capabilities, skip_counts)
    first.start()
    rpc_port2, p2p_port2 = free_ports(2)
    second = make_adapter(
        cls,
        executable,
        tmp_path / "second",
        rpc_port2,
        p2p_port2,
        extra_args=(f"-blocksdir={first_datadir}",),
    )
    try:
        with pytest.raises(
            RuntimeError, match=_lock_refusal(first_datadir / "regtest" / "blocks")
        ):
            second.start()
    finally:
        second.stop()
        first.stop()
