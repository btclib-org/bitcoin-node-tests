# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`fill_mempool`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/test_framework/mempool_util.py`:
`mempool_fill_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_fill_test import (
    fill_mempool_evicts_its_own_low_fee_rate_transaction,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_fill_mempool_evicts_its_own_low_fee_rate_transaction(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    fill_mempool_evicts_its_own_low_fee_rate_transaction(bitcoind_cluster, skip_counts)
