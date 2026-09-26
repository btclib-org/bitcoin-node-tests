# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_blocksdir.py` (`0d1301b47a35`,
2026-03-24) rather than ported whole: that file asserts a fresh node's
own `blocks_path` through Core's `TestNode`, mines ten blocks through the
framework's own deterministic wallet key, and reads `blk00000.dat` off
disk directly once `-blocksdir` redirects it. The middle step is
disk-family's own split (rule 4 of issue btclib-org/btclib#2220): reading
Core's own storage format is `Capability.BLK_FILES`
(`capability.py`), which nothing but this test asks for; the
`-blocksdir` startup refusal, the half kept whole, is a process fact
every `NodeAdapter` already answers (`node.py`'s own `start`), and this
repository's own adapter is what runs it, never Core's.

A smaller claim than Core's own, declared rather than silent: this mines
nothing. A fresh regtest node writes its genesis block to `blk00000.dat`
before a single block is mined, and the `-blocksdir` redirect this test
is about needs nothing more than that to show.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def _blocksdir_refusal(blocksdir: Path) -> str:
    """Return a pattern for Core's whole refusal of a nonexistent `blocksdir`.

    Core's file compares the whole message, the path included; anchored
    past `_wait_for_rpc`'s own `stderr: ` (`node.py`) and at the message's
    end, so that a stderr carrying anything beside the refusal fails it.
    """
    core = f'Error: Specified blocks directory "{blocksdir}" does not exist.'
    return rf"stderr: {re.escape(core)}\Z"


def test_nonexistent_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """`-blocksdir` naming a directory that does not exist is fatal."""
    blocksdir = tmp_path / "nonexistent"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path / "datadir",
        rpc_port,
        p2p_port,
        extra_args=(f"-blocksdir={blocksdir}",),
    )
    with pytest.raises(RuntimeError, match=_blocksdir_refusal(blocksdir)):
        adapter.start()


def test_existing_blocksdir_holds_the_chain_in_cores_own_files(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Core's own `blk00000.dat`, under the directory `-blocksdir` names."""
    blocksdir = tmp_path / "blocksdir"
    blocksdir.mkdir()
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path / "datadir",
        rpc_port,
        p2p_port,
        extra_args=(f"-blocksdir={blocksdir}",),
    )
    adapter.start()
    try:
        require(Capability.BLK_FILES, adapter.capabilities, skip_counts)
        assert (blocksdir / "regtest" / "blocks" / "blk00000.dat").is_file()
    finally:
        adapter.stop()
