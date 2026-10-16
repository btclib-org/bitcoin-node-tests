# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_invalidateblock`, rewritten on tf2's own harness: btcd.

`rpc_invalidateblock_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_invalidateblock_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_invalidateblock_test import (
    invalidateblock_and_reconsiderblock_move_the_tip,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_invalidateblock_and_reconsiderblock_move_the_tip(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    invalidateblock_and_reconsiderblock_move_the_tip(btcd_cluster, skip_counts)
