# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_remove_pruned_files_on_startup` on this harness: btclib-node.

`feature_remove_pruned_files_on_startup_test.py` beside this module is the
body, run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). It is a counted skip on `Capability.FASTPRUNE`,
asked for first: `cli.py` registers no `-fastprune`, measured at the
released `2026.9.24` and at `main` (`01a50073`) alike.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_remove_pruned_files_on_startup_test import (
    pruned_files_are_removed,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_pruned_files_are_removed(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: pruned block files removed, over btclib-node."""
    pruned_files_are_removed(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
