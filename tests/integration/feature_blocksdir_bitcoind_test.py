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

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_nonexistent_blocksdir_refuses_to_start(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """`-blocksdir` naming a directory that does not exist is fatal."""
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "datadir",
        free_port(),
        free_port(),
        extra_args=(f"-blocksdir={tmp_path / 'nonexistent'}",),
    )
    with pytest.raises(RuntimeError, match="exited"):
        adapter.start()


def test_existing_blocksdir_holds_the_chain_in_cores_own_files(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """Core's own `blk00000.dat`, under the directory `-blocksdir` names."""
    blocksdir = tmp_path / "blocksdir"
    blocksdir.mkdir()
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "datadir",
        free_port(),
        free_port(),
        extra_args=(f"-blocksdir={blocksdir}",),
    )
    adapter.start()
    try:
        require(Capability.BLK_FILES, adapter.capabilities, skip_counts)
        assert (blocksdir / "regtest" / "blocks" / "blk00000.dat").is_file()
    finally:
        adapter.stop()
