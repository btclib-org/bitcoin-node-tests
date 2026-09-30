# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_sendheaders`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/p2p_sendheaders.py`:
`p2p_sendheaders_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_sendheaders_test import (
    blocks_are_announced_by_headers_after_sendheaders,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_blocks_are_announced_by_headers_after_sendheaders(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    blocks_are_announced_by_headers_after_sendheaders(bitcoind_cluster, skip_counts)
