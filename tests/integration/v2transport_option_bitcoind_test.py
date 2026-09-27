# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--v2transport`, restated through the adapter: bitcoind.

`v2transport_option_test.py` beside this module holds each body, run
here against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.v2transport_option_test import (
    v2transport_0_connects_nodes_over_v1,
    v2transport_1_connects_nodes_over_bip324,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_v2transport_1_connects_nodes_over_bip324(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    v2transport_1_connects_nodes_over_bip324(bitcoind_cluster, skip_counts)


def test_v2transport_0_connects_nodes_over_v1(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    v2transport_0_connects_nodes_over_v1(bitcoind_cluster, skip_counts)
