# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_accept_wtxid`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/mempool_accept_wtxid.py`:
`mempool_accept_wtxid_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_accept_wtxid_test import (
    a_child_sharing_a_txid_is_told_apart_by_its_wtxid,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_child_sharing_a_txid_is_told_apart_by_its_wtxid(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_child_sharing_a_txid_is_told_apart_by_its_wtxid(bitcoind_cluster, skip_counts)
