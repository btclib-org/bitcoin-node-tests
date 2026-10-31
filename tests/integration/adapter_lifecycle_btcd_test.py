# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: btcd.

`adapter_lifecycle_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/adapter_lifecycle_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.adapter_lifecycle_test import (
    mine_extends_the_tip_by_the_blocks_it_returns,
    stop_reports_a_node_killed_out_from_under_it,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_stop_reports_a_node_killed_out_from_under_it(
    make_adapter: AdapterFactory, btcd_path: str, tmp_path: Path
) -> None:
    """The target: a node killed before `stop`."""
    stop_reports_a_node_killed_out_from_under_it(
        make_adapter, BtcdAdapter, btcd_path, tmp_path
    )


def test_mine_extends_the_tip_by_the_blocks_it_returns(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: each `mine` moves the tip onto its last hash."""
    mine_extends_the_tip_by_the_blocks_it_returns(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
