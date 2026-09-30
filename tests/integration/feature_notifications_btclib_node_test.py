# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_notifications`, rewritten on this harness: btclib-node.

`feature_notifications_test.py` beside this module has the bodies, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on the capability
naming its option, `Capability.BLOCK_NOTIFY`, `Capability.ALERT_NOTIFY`
or `Capability.SHUTDOWN_NOTIFY`, which `btclib_node.py`'s own docstring
has no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_notifications_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
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
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-blocknotify`'s command run per block, over btclib-node."""
    every_new_tip_is_notified(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_a_large_work_invalid_chain_is_alerted(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the invalid chain's warning notified, over btclib-node."""
    a_large_work_invalid_chain_is_alerted(
        make_adapter,
        BtclibNodeAdapter,
        btclib_node_python,
        tmp_path,
        skip_counts,
        lambda _node: True,
    )


def test_the_shutdown_is_notified(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-shutdownnotify`'s command run on stop, over btclib-node."""
    the_shutdown_is_notified(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
