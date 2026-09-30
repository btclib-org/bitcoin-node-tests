# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_invalidateblock`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/rpc_invalidateblock.py`:
`rpc_invalidateblock_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_invalidateblock_test import (
    invalidateblock_and_reconsiderblock_move_the_tip,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_invalidateblock_and_reconsiderblock_move_the_tip(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    invalidateblock_and_reconsiderblock_move_the_tip(bitcoind_cluster, skip_counts)
