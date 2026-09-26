# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_filelock.py` (`fa5f29774872`,
2025-12-16): a second process started over a datadir, or a blocksdir, a
first one already holds is fatal, disk-family mechanism alone
(issue btclib-org/btclib#2220,
[ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)) --
`NodeAdapter.start`'s own capture of a process's early exit (`node.py`)
is what every `assert_start_raises_init_error`-shaped test already
reads through.

A smaller claim than Core's own file, declared rather than silent: the
cookie- and PID-file persistence checks and the wallet-directory lock
are dropped. The first two are a fact about which files a node
happens to leave behind after a refused second start, not about the
lock itself; the third is a wallet fact, out of this suite's reach by
the charter's own rule.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


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


def test_second_instance_on_same_datadir_refuses_to_start(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """A second node over the same datadir cannot obtain its lock."""
    datadir = tmp_path / "datadir"
    first = BitcoindAdapter(bitcoind_path, datadir, free_port(), free_port())
    first.start()
    try:
        second = BitcoindAdapter(bitcoind_path, datadir, free_port(), free_port())
        with pytest.raises(RuntimeError, match=_lock_refusal(datadir / "regtest")):
            second.start()
    finally:
        first.stop()


def test_second_instance_on_same_blocksdir_refuses_to_start(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """A second node given the first's own datadir as `-blocksdir` fails."""
    first_datadir = tmp_path / "first"
    first = BitcoindAdapter(bitcoind_path, first_datadir, free_port(), free_port())
    first.start()
    try:
        second = BitcoindAdapter(
            bitcoind_path,
            tmp_path / "second",
            free_port(),
            free_port(),
            extra_args=(f"-blocksdir={first_datadir}",),
        )
        with pytest.raises(
            RuntimeError, match=_lock_refusal(first_datadir / "regtest" / "blocks")
        ):
            second.start()
    finally:
        first.stop()
