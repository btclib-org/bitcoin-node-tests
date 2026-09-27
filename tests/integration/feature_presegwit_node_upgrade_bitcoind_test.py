# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_presegwit_node_upgrade`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_presegwit_node_upgrade.py`:
`feature_presegwit_node_upgrade_test.py` beside this module is the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_presegwit_node_upgrade_test import (
    a_pre_segwit_chain_needs_a_reindex_to_upgrade,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_pre_segwit_chain_needs_a_reindex_to_upgrade(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_pre_segwit_chain_needs_a_reindex_to_upgrade(bitcoind_cluster, skip_counts)
