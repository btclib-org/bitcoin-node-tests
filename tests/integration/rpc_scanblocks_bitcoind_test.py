# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_scanblocks`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_scanblocks.py`:
`rpc_scanblocks_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_scanblocks_test import (
    scanblocks_finds_the_blocks_paying_what_it_is_asked_for,
    scanblocks_refuses_without_the_index,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_scanblocks_finds_the_blocks_paying_what_it_is_asked_for(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the scans the body module names, over bitcoind."""
    scanblocks_finds_the_blocks_paying_what_it_is_asked_for(
        bitcoind_cluster, skip_counts
    )


def test_scanblocks_refuses_without_the_index(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the refusal the body module names, over bitcoind."""
    scanblocks_refuses_without_the_index(bitcoind_cluster, skip_counts)
