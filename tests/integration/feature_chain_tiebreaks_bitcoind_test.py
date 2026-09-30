# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_chain_tiebreaks`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_chain_tiebreaks.py`:
`feature_chain_tiebreaks_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_chain_tiebreaks_test import (
    equal_work_tips_are_broken_by_arrival,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_equal_work_tips_are_broken_by_arrival(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    equal_work_tips_are_broken_by_arrival(bitcoind_cluster, skip_counts)
