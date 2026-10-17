# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_anchors`, rewritten on tf2's own harness: btcd.

`feature_anchors_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_anchors_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
from tests.integration.feature_anchors_test import (
    block_relay_only_peers_are_the_anchors,
    onion_anchor_is_dumped_and_dialled,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_block_relay_only_peers_are_the_anchors(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    block_relay_only_peers_are_the_anchors(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_onion_anchor_is_dumped_and_dialled(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    onion_anchor_is_dumped_and_dialled(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
