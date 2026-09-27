# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, rewritten on tf2's own harness: btclib-node.

`feature_blocksdir_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The refusal asks for no capability and runs;
reading the chain back off disk in Core's own `blk*.dat` layout is a
counted skip on `Capability.BLK_FILES`, which `btclib_node.py`'s own
docstring has no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_blocksdir_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_blocksdir_test import (
    a_nonexistent_blocksdir_refuses_to_start,
    an_existing_blocksdir_holds_the_chain_in_cores_own_files,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_nonexistent_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """The target: the refusal the body module names, over btclib-node."""
    a_nonexistent_blocksdir_refuses_to_start(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_existing_blocksdir_holds_the_chain_in_cores_own_files(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the files the body module names, over btclib-node."""
    an_existing_blocksdir_holds_the_chain_in_cores_own_files(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
