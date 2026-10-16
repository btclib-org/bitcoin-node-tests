# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_private_broadcast_retry_v1`, on tf2's own harness: btcd.

`p2p_private_broadcast_retry_v1_test.py` beside this module is the body,
run here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_private_broadcast_retry_v1_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
from tests.integration.p2p_private_broadcast_retry_v1_test import (
    v1_retry_goes_through_the_tor_proxy,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_v1_retry_goes_through_the_tor_proxy(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    v1_retry_goes_through_the_tor_proxy(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
