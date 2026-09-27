# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_initial_headers_sync`, on this repository's own harness.

Read from Core's `test/functional/p2p_initial_headers_sync.py`:
`p2p_initial_headers_sync_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_initial_headers_sync_test import (
    headers_are_asked_of_one_peer_per_announcement,
    headers_timeout_drops_the_peer,
    headers_timeout_is_logged,
    headers_timeout_keeps_a_noban_peer,
    headers_timeout_of_a_noban_peer_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_headers_are_asked_of_one_peer_per_announcement(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
) -> None:
    """The oracle: the check the body module names first, over bitcoind."""
    headers_are_asked_of_one_peer_per_announcement(bitcoind_cluster)


def test_headers_timeout_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    headers_timeout_drops_the_peer(bitcoind_cluster, skip_counts)


def test_headers_timeout_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    headers_timeout_is_logged(bitcoind_cluster, skip_counts)


def test_headers_timeout_keeps_a_noban_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    headers_timeout_keeps_a_noban_peer(bitcoind_cluster, skip_counts)


def test_headers_timeout_of_a_noban_peer_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    headers_timeout_of_a_noban_peer_is_logged(bitcoind_cluster, skip_counts)
