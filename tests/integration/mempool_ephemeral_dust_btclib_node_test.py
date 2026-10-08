# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_ephemeral_dust`, rewritten on tf2's own harness: btclib-node.

`mempool_ephemeral_dust_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The body with no relay floor and no package is
a counted skip on `Capability.MIN_RELAY_TX_FEE` on the released build,
which does not declare it, and runs on a build that does. The reorg body
runs on both builds. The released build fails it at the parent with a dust
output and a fee, and `main` passes it
([ISS btclib-node#1594](https://github.com/btclib-org/btclib-node/issues/1594)).
Every other one is a counted skip on `Capability.PACKAGE_ACCEPTANCE` where the
build does not declare it (`btclib_node.py`'s own docstring). Past it, a body
is a counted skip on the next capability it asks for that the build lacks, and
one asking for nothing the build lacks runs.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_ephemeral_dust_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_zero_value_dust_enters_with_the_package_spending_it(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    zero_value_dust_enters_with_the_package_spending_it(
        btclib_node_cluster, skip_counts
    )


def test_a_childless_dusty_parent_stays_unmined(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_childless_dusty_parent_stays_unmined(btclib_node_cluster, skip_counts)


def test_a_restart_drops_an_ephemeral_package(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_restart_drops_an_ephemeral_package(btclib_node_cluster, skip_counts)


def test_a_dusty_parent_paying_a_fee_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_dusty_parent_paying_a_fee_is_refused(btclib_node_cluster, skip_counts)


def test_a_parent_with_two_dust_outputs_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_parent_with_two_dust_outputs_is_refused(btclib_node_cluster, skip_counts)


def test_any_single_dust_output_is_allowed_alone(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    any_single_dust_output_is_allowed_alone(btclib_node_cluster, skip_counts)


def test_a_non_truc_dusty_parent_enters_with_its_spender(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_non_truc_dusty_parent_enters_with_its_spender(btclib_node_cluster, skip_counts)


def test_dust_left_unspent_refuses_the_child(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    dust_left_unspent_refuses_the_child(btclib_node_cluster, skip_counts)


def test_a_reorg_returns_dust_to_the_mempool_unchecked(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_reorg_returns_dust_to_the_mempool_unchecked(btclib_node_cluster, skip_counts)


def test_a_batch_sweep_must_spend_every_parents_dust(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_batch_sweep_must_spend_every_parents_dust(btclib_node_cluster, skip_counts)
