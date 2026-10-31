# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_remove_pruned_files_on_startup` on tf2's own harness: btcd.

`feature_remove_pruned_files_on_startup_test.py` beside this module is
the body, run here against btcd, a target rather than the oracle (rule 3
of issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration \
        -k feature_remove_pruned_files_on_startup_btcd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.feature_remove_pruned_files_on_startup_test import (
    pruned_files_are_removed,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_pruned_files_are_removed(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: pruned block files removed, over btcd."""
    pruned_files_are_removed(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
