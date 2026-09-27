# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addrfetch`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_addrfetch.py`: `p2p_addrfetch_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_addrfetch_test import (
    addr_fetch_peer_is_asked_for_addresses_and_dropped_on_many,
    addr_fetch_peer_sending_nothing_is_dropped_after_five_minutes,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_addr_fetch_peer_is_asked_for_addresses_and_dropped_on_many(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    addr_fetch_peer_is_asked_for_addresses_and_dropped_on_many(
        bitcoind_cluster, skip_counts
    )


def test_addr_fetch_peer_sending_nothing_is_dropped_after_five_minutes(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    addr_fetch_peer_sending_nothing_is_dropped_after_five_minutes(
        bitcoind_cluster, skip_counts
    )
