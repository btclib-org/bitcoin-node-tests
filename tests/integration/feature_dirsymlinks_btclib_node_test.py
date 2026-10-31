# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dirsymlinks`, rewritten on this harness: btclib-node.

`feature_dirsymlinks_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_dirsymlinks_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_dirsymlinks_test import (
    starts_with_symlinked_blocks_and_chainstate_directories,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_starts_with_symlinked_blocks_and_chainstate_directories(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """The target: a restart over symlinked directories, over btclib-node."""
    starts_with_symlinked_blocks_and_chainstate_directories(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )
