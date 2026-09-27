# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_sigoplimit`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_sigoplimit.py`:
`mempool_sigoplimit_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_sigoplimit_test import (
    a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize(
        bitcoind_cluster, skip_counts
    )
