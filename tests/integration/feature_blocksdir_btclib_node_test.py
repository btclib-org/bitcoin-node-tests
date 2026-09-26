# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, rewritten on tf2's own harness: btclib-node.

The same two claims `feature_blocksdir_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220): a nonexistent `-blocksdir` is fatal on both
nodes, `Config.__init__`'s own refusal (`src/btclib_node/config.py`);
reading the chain back off disk in Core's own `blk*.dat` layout is not,
`Capability.BLK_FILES` never being declared here (`btclib_node.py`'s own
docstring has why), so that half counts a skip rather than a silent
pass.

Two wordings of the refusal are live across the builds this suite runs
against, and the match below accepts either, each whole and naming the
path given, rather than picking one: the smaller design against a
version switch, as in `feature_filelock_btclib_node_test.py`. The
released build (PyPI, `2026.9.24`) writes its own `btclib-node:
specified blocks directory <path> does not exist`; `main`, past
[ISS btclib-node#1191](https://github.com/btclib-org/btclib-node/issues/1191),
writes Core's own `Error: Specified blocks directory "<path>" does not
exist.`, the whole text Core's `feature_blocksdir.py` compares.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_blocksdir_btclib_node_test.py
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def _blocksdir_refusal(blocksdir: Path) -> str:
    """Return a pattern for the whole stderr refusing a nonexistent `blocksdir`.

    Anchored past `_wait_for_rpc`'s own `stderr: ` (`node.py`) and at the
    message's end, so that a stderr carrying anything beside the refusal
    fails it; the released build's own wording is alternated with Core's,
    which `main` writes -- see the module docstring.
    """
    core = re.escape(f'Error: Specified blocks directory "{blocksdir}" does not exist.')
    released = re.escape(
        f"btclib-node: specified blocks directory {blocksdir} does not exist"
    )
    return rf"stderr: (?:{core}|{released})\Z"


def test_nonexistent_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """`-blocksdir` naming a directory that does not exist is fatal."""
    blocksdir = tmp_path / "nonexistent"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter,
        btclib_node_python,
        tmp_path / "datadir",
        rpc_port,
        p2p_port,
        extra_args=(f"-blocksdir={blocksdir}",),
    )
    with pytest.raises(RuntimeError, match=_blocksdir_refusal(blocksdir)):
        adapter.start()


def test_existing_blocksdir_holds_the_chain_in_cores_own_files(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.BLK_FILES` is not declared, so this counts a skip.

    Checked before a node is ever spawned: the capability is the class's
    own, unconditional on the instance, so there is nothing here for a
    running process to add to the answer. `btclib_node_python` is asked
    for anyway -- unused otherwise -- so that this still skips itself
    without `TF2_INTEGRATION`, the way every other test under
    `tests/integration/` does, rather than running unconditionally for
    having no other fixture left to gate it.
    """
    del btclib_node_python
    require(Capability.BLK_FILES, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
