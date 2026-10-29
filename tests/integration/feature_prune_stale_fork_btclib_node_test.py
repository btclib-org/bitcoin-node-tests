# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_prune_stale_fork` on this harness: btclib-node.

`feature_prune_stale_fork_test.py` beside this module is the
body, run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). It is a counted skip on `Capability.FASTPRUNE`,
asked for first, which `BtclibNodeAdapter` declares on no build.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_prune_stale_fork_test import (
    a_pruned_stale_fork_survives_a_restart,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_pruned_stale_fork_survives_a_restart(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a pruned stale fork survives a restart, over btclib-node."""
    a_pruned_stale_fork_survives_a_restart(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
