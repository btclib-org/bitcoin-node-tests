# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ping`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_ping.py`: `p2p_ping_test.py` beside
this module is the body, run here against bitcoind, which declares every
capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ping_test import (
    ping_replies_are_logged,
    ping_replies_are_reported_on_rpc,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_ping_replies_are_reported_on_rpc(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    ping_replies_are_reported_on_rpc(bitcoind_cluster, skip_counts)


def test_ping_replies_are_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    ping_replies_are_logged(bitcoind_cluster, skip_counts)
