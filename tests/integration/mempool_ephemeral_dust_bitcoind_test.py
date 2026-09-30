# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_ephemeral_dust`, rewritten on this repository's own harness.

Read from Core's `test/functional/mempool_ephemeral_dust.py`:
`mempool_ephemeral_dust_test.py` beside this module holds each body, run
here against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_zero_value_dust_enters_with_the_package_spending_it(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    zero_value_dust_enters_with_the_package_spending_it(bitcoind_cluster, skip_counts)


def test_a_childless_dusty_parent_stays_unmined(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_childless_dusty_parent_stays_unmined(bitcoind_cluster, skip_counts)


def test_a_restart_drops_an_ephemeral_package(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_restart_drops_an_ephemeral_package(bitcoind_cluster, skip_counts)


def test_a_dusty_parent_paying_a_fee_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_dusty_parent_paying_a_fee_is_refused(bitcoind_cluster, skip_counts)


def test_a_parent_with_two_dust_outputs_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_parent_with_two_dust_outputs_is_refused(bitcoind_cluster, skip_counts)


def test_any_single_dust_output_is_allowed_alone(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    any_single_dust_output_is_allowed_alone(bitcoind_cluster, skip_counts)


def test_a_non_truc_dusty_parent_enters_with_its_spender(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_non_truc_dusty_parent_enters_with_its_spender(bitcoind_cluster, skip_counts)


def test_dust_left_unspent_refuses_the_child(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    dust_left_unspent_refuses_the_child(bitcoind_cluster, skip_counts)


def test_a_reorg_returns_dust_to_the_mempool_unchecked(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_reorg_returns_dust_to_the_mempool_unchecked(bitcoind_cluster, skip_counts)


def test_a_batch_sweep_must_spend_every_parents_dust(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_batch_sweep_must_spend_every_parents_dust(bitcoind_cluster, skip_counts)
