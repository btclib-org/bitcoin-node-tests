# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_nulldummy`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_nulldummy.py`:
`feature_nulldummy_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_nulldummy_test import (
    nulldummy_is_policy_before_activation_and_consensus_after,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_nulldummy_is_policy_before_activation_and_consensus_after(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    nulldummy_is_policy_before_activation_and_consensus_after(
        bitcoind_cluster, skip_counts
    )
