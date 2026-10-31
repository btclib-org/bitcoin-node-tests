# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_ephemeral_dust`, rewritten on tf2's own harness: btcd.

`mempool_ephemeral_dust_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_ephemeral_dust_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_ephemeral_dust_test import (
    a_batch_sweep_must_spend_every_parents_dust,
    a_childless_dusty_parent_stays_unmined,
    a_dusty_parent_paying_a_fee_is_refused,
    a_non_truc_dusty_parent_enters_with_its_spender,
    a_parent_with_two_dust_outputs_is_refused,
    a_reorg_returns_dust_to_the_mempool_unchecked,
    a_restart_drops_an_ephemeral_package,
    any_single_dust_output_is_allowed_alone,
    dust_left_unspent_refuses_the_child,
    zero_value_dust_enters_with_the_package_spending_it,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_zero_value_dust_enters_with_the_package_spending_it(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    zero_value_dust_enters_with_the_package_spending_it(btcd_cluster, skip_counts)


def test_a_childless_dusty_parent_stays_unmined(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_childless_dusty_parent_stays_unmined(btcd_cluster, skip_counts)


def test_a_restart_drops_an_ephemeral_package(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_restart_drops_an_ephemeral_package(btcd_cluster, skip_counts)


def test_a_dusty_parent_paying_a_fee_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_dusty_parent_paying_a_fee_is_refused(btcd_cluster, skip_counts)


def test_a_parent_with_two_dust_outputs_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_parent_with_two_dust_outputs_is_refused(btcd_cluster, skip_counts)


def test_any_single_dust_output_is_allowed_alone(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    any_single_dust_output_is_allowed_alone(btcd_cluster, skip_counts)


def test_a_non_truc_dusty_parent_enters_with_its_spender(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_non_truc_dusty_parent_enters_with_its_spender(btcd_cluster, skip_counts)


def test_dust_left_unspent_refuses_the_child(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    dust_left_unspent_refuses_the_child(btcd_cluster, skip_counts)


def test_a_reorg_returns_dust_to_the_mempool_unchecked(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_reorg_returns_dust_to_the_mempool_unchecked(btcd_cluster, skip_counts)


def test_a_batch_sweep_must_spend_every_parents_dust(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_batch_sweep_must_spend_every_parents_dust(btcd_cluster, skip_counts)
