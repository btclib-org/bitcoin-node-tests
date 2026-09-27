# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_timeouts`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_timeouts.py`: `p2p_timeouts_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_timeouts_test import (
    a_non_positive_peertimeout_is_refused,
    handshake_timeouts_are_logged,
    peers_that_never_finish_the_handshake_are_dropped,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_peers_that_never_finish_the_handshake_are_dropped(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    peers_that_never_finish_the_handshake_are_dropped(bitcoind_cluster, skip_counts)


def test_handshake_timeouts_are_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    handshake_timeouts_are_logged(bitcoind_cluster, skip_counts)


def test_a_non_positive_peertimeout_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the refused start the body module names, over bitcoind."""
    a_non_positive_peertimeout_is_refused(bitcoind_cluster, skip_counts)
