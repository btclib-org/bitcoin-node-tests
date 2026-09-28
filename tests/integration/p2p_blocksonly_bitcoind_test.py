# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_blocksonly`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/p2p_blocksonly.py`:
`p2p_blocksonly_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_blocksonly_test import (
    a_block_relay_only_peer_is_refused_transactions,
    a_block_relay_only_peer_refusal_is_logged,
    a_blocksonly_node_refusal_is_logged,
    a_blocksonly_node_refuses_transactions,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_block_relay_only_peer_is_refused_transactions(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_block_relay_only_peer_is_refused_transactions(bitcoind_cluster, skip_counts)


def test_a_block_relay_only_peer_refusal_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_block_relay_only_peer_refusal_is_logged(bitcoind_cluster, skip_counts)


def test_a_blocksonly_node_refuses_transactions(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_blocksonly_node_refuses_transactions(bitcoind_cluster, skip_counts)


def test_a_blocksonly_node_refusal_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_blocksonly_node_refusal_is_logged(bitcoind_cluster, skip_counts)
