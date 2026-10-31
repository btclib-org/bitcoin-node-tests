# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, one body over each node.

Read from Core's `test/functional/feature_blocksdir.py` (`0d1301b47a35`,
2026-03-24) rather than ported whole: that file asserts a fresh node's
own `blocks_path` through Core's `TestNode`, mines ten blocks through the
framework's own deterministic wallet key, and reads `blk00000.dat` off
disk directly once `-blocksdir` redirects it. The middle step is
disk-family's own split (rule 4 of issue btclib-org/btclib#2220): reading
Core's own storage format is `Capability.BLK_FILES`
(`capability.py`), which nothing but this test asks for; the
`-blocksdir` startup refusal, the half kept whole, is a process fact
(`node.py`'s own `start`) of a node that reads the option, which is
`Capability.BLOCKS_DIR` (`capability.py`); this repository's own adapter
is what runs it, never Core's.

A smaller claim than Core's own, declared rather than silent: this mines
nothing. A fresh regtest node writes its genesis block to `blk00000.dat`
before a single block is mined, and the `-blocksdir` redirect this test
is about needs nothing more than that to show.

The refusal is Core's own wording alone, `Error: Specified blocks
directory "<path>" does not exist.`, compared whole as Core's file
compares it. btclib-node writes it past
[ISS btclib-node#1416](https://github.com/btclib-org/btclib-node/issues/1416);
the released `2026.9.24` writes its own wording, and fails.

Each test builds its node over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since it gives the
node `-blocksdir` from its first start.
Each `feature_blocksdir_<node>_test.py` module beside this one runs it,
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
    "a_nonexistent_blocksdir_refuses_to_start",
    "an_existing_blocksdir_holds_the_chain_in_cores_own_files",
]


def _blocksdir_refusal(blocksdir: Path) -> str:
    """Return a pattern for Core's whole refusal of a nonexistent `blocksdir`.

    Core's file compares the whole message, the path included; anchored
    past `_wait_for_rpc`'s own `stderr: ` (`node.py`) and at the message's
    end, so that a stderr carrying anything beside the refusal fails it.
    """
    core = f'Error: Specified blocks directory "{blocksdir}" does not exist.'
    return rf"stderr: {re.escape(core)}\Z"


def _node(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    blocksdir: Path,
    skip_counts: SkipCounts,
) -> NodeAdapter:
    """Return a node given `-blocksdir`, not yet started, on ports of its own.

    The capability is asked of a node built without the option: a node
    that reads `-blocksdir` as another option refuses the construction.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param blocksdir: what `-blocksdir` names.
    :param skip_counts: the session's own tally.
    """
    rpc_port, p2p_port = free_ports(2)
    probe = make_adapter(cls, executable, tmp_path / "probe", rpc_port, p2p_port)
    require(Capability.BLOCKS_DIR, probe.capabilities, skip_counts)
    return make_adapter(
        cls,
        executable,
        tmp_path / "datadir",
        rpc_port,
        p2p_port,
        extra_args=(f"-blocksdir={blocksdir}",),
    )


def a_nonexistent_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-blocksdir` naming a directory that does not exist is fatal.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    blocksdir = tmp_path / "nonexistent"
    node = _node(make_adapter, cls, executable, tmp_path, blocksdir, skip_counts)
    try:
        with pytest.raises(RuntimeError, match=_blocksdir_refusal(blocksdir)):
            node.start()
    finally:
        node.stop()


def an_existing_blocksdir_holds_the_chain_in_cores_own_files(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check Core's own `blk00000.dat` is under the `-blocksdir` given.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    blocksdir = tmp_path / "blocksdir"
    blocksdir.mkdir()
    node = _node(make_adapter, cls, executable, tmp_path, blocksdir, skip_counts)
    require(Capability.BLK_FILES, node.capabilities, skip_counts)
    try:
        node.start()
        assert (blocksdir / "regtest" / "blocks" / "blk00000.dat").is_file()
    finally:
        node.stop()
