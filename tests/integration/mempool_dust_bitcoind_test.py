# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_dust`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_dust.py`:
`mempool_dust_test.py` beside this module holds each body, run here
against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_dust_test import (
    a_value_clearly_above_the_dust_threshold_is_allowed,
    a_value_clearly_below_the_dust_threshold_is_refused,
    dustrelayfee_zero_waives_the_dust_check,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_value_clearly_below_the_dust_threshold_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_value_clearly_below_the_dust_threshold_is_refused(bitcoind_cluster, skip_counts)


def test_a_value_clearly_above_the_dust_threshold_is_allowed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_value_clearly_above_the_dust_threshold_is_allowed(bitcoind_cluster, skip_counts)


def test_dustrelayfee_zero_waives_the_dust_check(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    dustrelayfee_zero_waives_the_dust_check(bitcoind_cluster, skip_counts)
