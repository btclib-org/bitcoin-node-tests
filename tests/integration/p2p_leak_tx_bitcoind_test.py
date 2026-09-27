# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak_tx`, rewritten on this repository's own harness: bitcoind.

Read from Core's `test/functional/p2p_leak_tx.py`: `p2p_leak_tx_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_leak_tx_test import (
    notfound_on_replaced_tx,
    notfound_on_unannounced_tx,
    tx_in_block,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_tx_in_block(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a tx just mined into the tip's block is still uploaded."""
    tx_in_block(bitcoind_cluster, skip_counts)


def test_notfound_on_replaced_tx(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a getdata for a replaced tx answers notfound."""
    notfound_on_replaced_tx(bitcoind_cluster, skip_counts)


def test_notfound_on_unannounced_tx(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a getdata for a tx not yet announced answers notfound."""
    notfound_on_unannounced_tx(bitcoind_cluster, skip_counts)
