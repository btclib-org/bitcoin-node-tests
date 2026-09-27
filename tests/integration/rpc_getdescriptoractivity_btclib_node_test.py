# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_getdescriptoractivity`, on tf2's own harness: btclib-node.

`rpc_getdescriptoractivity_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DESCRIPTOR_ACTIVITY` is not
declared (`btclib_node.py`'s own docstring is why: `getdescriptoractivity`
names no callback in its dispatch table, on either build), so every
test is a counted skip ahead of `Capability.MINE`, which the tests
needing a `MiniWallet` also ask for.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/rpc_getdescriptoractivity_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_getdescriptoractivity_test import (
    activity_in_block,
    confirmed_and_unconfirmed,
    invalid_blockhash,
    invalid_descriptor,
    multiple_addresses,
    no_activity_for_an_unused_address,
    no_address,
    no_mempool_inclusion,
    receive_then_spend,
    required_args,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_no_activity_for_an_unused_address(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    no_activity_for_an_unused_address(btclib_node_adapter, skip_counts)


def test_activity_in_block(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    activity_in_block(btclib_node_cluster, skip_counts)


def test_no_mempool_inclusion(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    no_mempool_inclusion(btclib_node_cluster, skip_counts)


def test_invalid_blockhash(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    invalid_blockhash(btclib_node_adapter, skip_counts)


def test_invalid_descriptor(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    invalid_descriptor(btclib_node_adapter, skip_counts)


def test_required_args(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btclib-node."""
    required_args(btclib_node_adapter, skip_counts)


def test_multiple_addresses(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    multiple_addresses(btclib_node_cluster, skip_counts)


def test_confirmed_and_unconfirmed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    confirmed_and_unconfirmed(btclib_node_cluster, skip_counts)


def test_receive_then_spend(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    receive_then_spend(btclib_node_cluster, skip_counts)


def test_no_address(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btclib-node."""
    no_address(btclib_node_cluster, skip_counts)
