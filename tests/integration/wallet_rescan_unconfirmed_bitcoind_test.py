# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_rescan_unconfirmed`, on this harness: bitcoind.

Read from Core's `test/functional/wallet_rescan_unconfirmed.py`:
`wallet_rescan_unconfirmed_test.py` beside this module holds the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_rescan_unconfirmed_test import (
    an_import_rescans_a_child_back_in_the_mempool_before_its_parent,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_an_import_rescans_a_child_back_in_the_mempool_before_its_parent(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_import_rescans_a_child_back_in_the_mempool_before_its_parent(
        bitcoind_cluster, skip_counts
    )
