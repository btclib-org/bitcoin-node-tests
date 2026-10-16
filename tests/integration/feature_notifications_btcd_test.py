# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_notifications`, rewritten on tf2's own harness: btcd.

`feature_notifications_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_notifications_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
from tests.integration.feature_notifications_test import (
    a_large_work_invalid_chain_is_alerted,
    every_new_tip_is_notified,
    the_shutdown_is_notified,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_every_new_tip_is_notified(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-blocknotify`'s command run per block, over btcd."""
    every_new_tip_is_notified(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_large_work_invalid_chain_is_alerted(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the invalid chain's warning notified, over btcd."""
    a_large_work_invalid_chain_is_alerted(
        make_adapter,
        BtcdAdapter,
        btcd_path,
        tmp_path,
        skip_counts,
        lambda _node: True,
    )


def test_the_shutdown_is_notified(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-shutdownnotify`'s command run on stop, over btcd."""
    the_shutdown_is_notified(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
