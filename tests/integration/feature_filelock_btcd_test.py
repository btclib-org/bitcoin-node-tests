# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, rewritten on tf2's own harness: btcd.

`feature_filelock_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_filelock_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.feature_filelock_test import (
    second_instance_on_same_blocksdir_refuses_to_start,
    second_instance_on_same_datadir_refuses_to_start,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_second_instance_on_same_datadir_refuses_to_start(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
) -> None:
    """The target: a second node over the same datadir is refused."""
    second_instance_on_same_datadir_refuses_to_start(
        make_adapter, BtcdAdapter, btcd_path, tmp_path
    )


def test_second_instance_on_same_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a second node over the first's blocksdir is refused."""
    second_instance_on_same_blocksdir_refuses_to_start(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
