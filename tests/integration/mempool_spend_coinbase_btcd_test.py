# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_spend_coinbase`, rewritten on tf2's own harness: btcd.

`mempool_spend_coinbase_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_spend_coinbase_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_spend_coinbase_test import (
    a_mature_coinbase_spends_and_an_immature_one_is_refused,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_mature_coinbase_spends_and_an_immature_one_is_refused(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_mature_coinbase_spends_and_an_immature_one_is_refused(btcd_adapter, skip_counts)
