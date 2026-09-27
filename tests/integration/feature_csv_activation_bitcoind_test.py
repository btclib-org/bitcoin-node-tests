# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_csv_activation`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_csv_activation.py`:
`feature_csv_activation_test.py` beside this module holds the bodies, run
here against bitcoind.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_csv_activation_test import (
    csv_activates_one_block_before_the_configured_height,
    csv_rules_are_enforced_from_the_configured_height,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_csv_activates_one_block_before_the_configured_height(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `getdeploymentinfo`'s own `csv` entry."""
    csv_activates_one_block_before_the_configured_height(bitcoind_cluster, skip_counts)


def test_csv_rules_are_enforced_from_the_configured_height(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `submitblock`'s own answer to each of Core's blocks."""
    csv_rules_are_enforced_from_the_configured_height(bitcoind_cluster, skip_counts)
