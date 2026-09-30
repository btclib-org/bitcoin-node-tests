# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ibd_txrelay`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_ibd_txrelay.py`:
`p2p_ibd_txrelay_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ibd_txrelay_test import (
    ibd_tx_relay_is_logged,
    ibd_tx_relay_is_withheld,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_ibd_tx_relay_is_withheld(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    ibd_tx_relay_is_withheld(bitcoind_cluster, skip_counts)


def test_ibd_tx_relay_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    ibd_tx_relay_is_logged(bitcoind_cluster, skip_counts)
