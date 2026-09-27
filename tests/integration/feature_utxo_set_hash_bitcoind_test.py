# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_utxo_set_hash`, rewritten on this repository's own harness.

Read from Core's `test/functional/feature_utxo_set_hash.py`:
`feature_utxo_set_hash_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_utxo_set_hash_test import (
    independent_muhash_matches_gettxoutsetinfo,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_independent_muhash_matches_gettxoutsetinfo(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    independent_muhash_matches_gettxoutsetinfo(bitcoind_adapter, skip_counts)
