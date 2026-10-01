# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_headers_sync_with_minchainwork`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/p2p_headers_sync_with_minchainwork.py`:
`p2p_headers_sync_with_minchainwork_test.py` beside this module is the
body, run here against bitcoind, which declares every capability it asks
for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_headers_sync_with_minchainwork_test import (
    TEST_TIMEOUT,
    low_work_headers_are_ignored_until_the_chain_has_the_work,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


@pytest.mark.scaled_timeout(TEST_TIMEOUT)
def test_low_work_headers_are_ignored_until_the_chain_has_the_work(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    low_work_headers_are_ignored_until_the_chain_has_the_work(
        bitcoind_cluster, skip_counts
    )
