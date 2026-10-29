# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_prune_stale_fork` on tf2's own harness: btcd.

`feature_prune_stale_fork_test.py` beside this module is
the body, run here against btcd, a target rather than the oracle (rule 3
of issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration \
        -k feature_prune_stale_fork_btcd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
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
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a pruned stale fork survives a restart, over btcd."""
    a_pruned_stale_fork_survives_a_restart(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
