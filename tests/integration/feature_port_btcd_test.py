# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_port`, rewritten on tf2's own harness: btcd.

`feature_port_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_port_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
from tests.integration.feature_port_test import (
    port_and_bind_decide_where_the_node_listens,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_port_and_bind_decide_where_the_node_listens(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: where `-port` and `-bind` have btcd listen."""
    port_and_bind_decide_where_the_node_listens(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
