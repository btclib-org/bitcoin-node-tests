# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_coinbase_category`, on this harness: bitcoind.

Read from Core's `test/functional/wallet_coinbase_category.py`:
`wallet_coinbase_category_test.py` beside this module holds the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_coinbase_category_test import (
    a_coinbase_is_immature_then_generate_then_orphan,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_coinbase_is_immature_then_generate_then_orphan(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_coinbase_is_immature_then_generate_then_orphan(bitcoind_cluster, skip_counts)
