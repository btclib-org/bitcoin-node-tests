# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_outbound_eviction`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_outbound_eviction.py`:
`p2p_outbound_eviction_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_outbound_eviction_test import (
    block_relay_only_peer_is_not_protected,
    lagging_unprotected_peers_are_evicted,
    only_misbehaving_unprotected_peers_are_evicted,
    protected_peer_is_not_evicted,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_lagging_unprotected_peers_are_evicted(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    lagging_unprotected_peers_are_evicted(bitcoind_cluster, skip_counts)


def test_protected_peer_is_not_evicted(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    protected_peer_is_not_evicted(bitcoind_cluster, skip_counts)


def test_only_misbehaving_unprotected_peers_are_evicted(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    only_misbehaving_unprotected_peers_are_evicted(bitcoind_cluster, skip_counts)


def test_block_relay_only_peer_is_not_protected(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    block_relay_only_peer_is_not_protected(bitcoind_cluster, skip_counts)
