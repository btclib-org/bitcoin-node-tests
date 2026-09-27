# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_mutated_blocks`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_mutated_blocks.py`:
`p2p_mutated_blocks_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_mutated_blocks_test import (
    block_missing_its_parent_drops_the_peer,
    block_missing_its_parent_is_logged,
    mutated_block_is_logged,
    mutated_block_keeps_the_honest_request,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mutated_block_keeps_the_honest_request(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mutated_block_keeps_the_honest_request(bitcoind_cluster, skip_counts)


def test_mutated_block_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    mutated_block_is_logged(bitcoind_cluster, skip_counts)


def test_block_missing_its_parent_drops_the_peer(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    block_missing_its_parent_drops_the_peer(bitcoind_cluster, skip_counts)


def test_block_missing_its_parent_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    block_missing_its_parent_is_logged(bitcoind_cluster, skip_counts)
