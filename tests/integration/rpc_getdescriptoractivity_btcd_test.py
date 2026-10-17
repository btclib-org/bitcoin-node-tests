# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptoractivity`, on tf2's own harness: btcd.

`rpc_getdescriptoractivity_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_getdescriptoractivity_btcd_test.py
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

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_no_activity_for_an_unused_address(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body of the same name, over btcd."""
    no_activity_for_an_unused_address(btcd_adapter, skip_counts)


def test_activity_in_block(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    activity_in_block(btcd_cluster, skip_counts)


def test_no_mempool_inclusion(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    no_mempool_inclusion(btcd_cluster, skip_counts)


def test_invalid_blockhash(btcd_adapter: BtcdAdapter, skip_counts: SkipCounts) -> None:
    """The target: the body of the same name, over btcd."""
    invalid_blockhash(btcd_adapter, skip_counts)


def test_invalid_descriptor(btcd_adapter: BtcdAdapter, skip_counts: SkipCounts) -> None:
    """The target: the body of the same name, over btcd."""
    invalid_descriptor(btcd_adapter, skip_counts)


def test_required_args(btcd_adapter: BtcdAdapter, skip_counts: SkipCounts) -> None:
    """The target: the body of the same name, over btcd."""
    required_args(btcd_adapter, skip_counts)


def test_multiple_addresses(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    multiple_addresses(btcd_cluster, skip_counts)


def test_confirmed_and_unconfirmed(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    confirmed_and_unconfirmed(btcd_cluster, skip_counts)


def test_receive_then_spend(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    receive_then_spend(btcd_cluster, skip_counts)


def test_no_address(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body of the same name, over btcd."""
    no_address(btcd_cluster, skip_counts)
