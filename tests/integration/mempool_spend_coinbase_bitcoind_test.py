# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_spend_coinbase`, rewritten on this repository's own harness.

Read from Core's `test/functional/mempool_spend_coinbase.py`:
`mempool_spend_coinbase_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_spend_coinbase_test import (
    a_mature_coinbase_spends_and_an_immature_one_is_refused,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_mature_coinbase_spends_and_an_immature_one_is_refused(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_mature_coinbase_spends_and_an_immature_one_is_refused(
        bitcoind_adapter, skip_counts
    )
