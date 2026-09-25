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

`btclib_node`'s own chainstate and block databases are each their own
`Rdict` (RocksDB), which takes an exclusive lock on its own directory:
measured live, a second `python -m btclib_node` pointed at a datadir (or
a blocksdir) already open exits 1 with an uncaught `Exception: IO
error: While lock file: <path>/LOCK: Resource temporarily unavailable`
-- the same category of fact bitcoind's own "Cannot obtain a lock on
directory" names, in this node's own wording rather than a friendly
message of its own. That the exception is uncaught, where bitcoind's
own is a clean init error, is
[ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147),
filed on that repository's own tracker; the match below is against this
node's own traceback text and is unaffected by whether it is caught.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_filelock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


def test_second_instance_on_same_datadir_refuses_to_start(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node over the same datadir cannot lock its own chainstate."""
    datadir = tmp_path / "datadir"
    first = BtclibNodeAdapter(btclib_node_python, datadir, free_port(), free_port())
    first.start()
    try:
        second = BtclibNodeAdapter(
            btclib_node_python, datadir, free_port(), free_port()
        )
        with pytest.raises(RuntimeError, match=r"chainstate[/\\]LOCK"):
            second.start()
    finally:
        first.stop()


def test_second_instance_on_same_blocksdir_refuses_to_start(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """A second node given the first's own datadir as `-blocksdir` fails."""
    first_datadir = tmp_path / "first"
    first = BtclibNodeAdapter(
        btclib_node_python, first_datadir, free_port(), free_port()
    )
    first.start()
    try:
        second = BtclibNodeAdapter(
            btclib_node_python,
            tmp_path / "second",
            free_port(),
            free_port(),
            extra_args=(f"-blocksdir={first_datadir}",),
        )
        with pytest.raises(RuntimeError, match=r"blocks[/\\]LOCK"):
            second.start()
    finally:
        first.stop()
