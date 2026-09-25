# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, rewritten on tf2's own harness: btclib-node.

The same two claims `feature_blocksdir_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220): a nonexistent `-blocksdir` is fatal on both
nodes, `Config.__init__`'s own refusal
(`src/btclib_node/config.py`) matching Core's wording that module's own
docstring quotes; reading the chain back off disk in Core's own
`blk*.dat` layout is not, `Capability.BLK_FILES` never being declared
here (`btclib_node.py`'s own docstring has why), so that half counts a
skip rather than a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_blocksdir_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_nonexistent_blocksdir_refuses_to_start(
    btclib_node_python: str, tmp_path: Path
) -> None:
    """`-blocksdir` naming a directory that does not exist is fatal."""
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        tmp_path / "datadir",
        free_port(),
        free_port(),
        extra_args=(f"-blocksdir={tmp_path / 'nonexistent'}",),
    )
    with pytest.raises(RuntimeError, match="exited"):
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
