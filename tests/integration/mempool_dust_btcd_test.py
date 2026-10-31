# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_dust`, rewritten on tf2's own harness: btcd.

`mempool_dust_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_dust_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_value_clearly_below_the_dust_threshold_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_value_clearly_below_the_dust_threshold_is_refused(btcd_cluster, skip_counts)


def test_a_value_clearly_above_the_dust_threshold_is_allowed(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_value_clearly_above_the_dust_threshold_is_allowed(btcd_cluster, skip_counts)


def test_dustrelayfee_zero_waives_the_dust_check(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    dustrelayfee_zero_waives_the_dust_check(btcd_cluster, skip_counts)
