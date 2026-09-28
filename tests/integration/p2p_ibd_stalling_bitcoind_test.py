# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ibd_stalling`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_ibd_stalling.py`:
`p2p_ibd_stalling_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ibd_stalling_test import (
    manual_peer_stalling_is_logged,
    manual_peer_stalling_pauses_the_peer,
    stalling_drops_the_staller,
    stalling_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_stalling_drops_the_staller(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    stalling_drops_the_staller(bitcoind_cluster, skip_counts)


def test_stalling_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    stalling_is_logged(bitcoind_cluster, skip_counts)


def test_manual_peer_stalling_pauses_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    manual_peer_stalling_pauses_the_peer(bitcoind_cluster, skip_counts)


def test_manual_peer_stalling_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    manual_peer_stalling_is_logged(bitcoind_cluster, skip_counts)
