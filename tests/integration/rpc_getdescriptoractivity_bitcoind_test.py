# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptoractivity`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getdescriptoractivity.py`:
`rpc_getdescriptoractivity_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_no_activity_for_an_unused_address(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    no_activity_for_an_unused_address(bitcoind_adapter, skip_counts)


def test_activity_in_block(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    activity_in_block(bitcoind_cluster, skip_counts)


def test_no_mempool_inclusion(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    no_mempool_inclusion(bitcoind_cluster, skip_counts)


def test_invalid_blockhash(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    invalid_blockhash(bitcoind_adapter, skip_counts)


def test_invalid_descriptor(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    invalid_descriptor(bitcoind_adapter, skip_counts)


def test_required_args(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    required_args(bitcoind_adapter, skip_counts)


def test_multiple_addresses(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    multiple_addresses(bitcoind_cluster, skip_counts)


def test_confirmed_and_unconfirmed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    confirmed_and_unconfirmed(bitcoind_cluster, skip_counts)


def test_receive_then_spend(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    receive_then_spend(bitcoind_cluster, skip_counts)


def test_no_address(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body of the same name, over bitcoind."""
    no_address(bitcoind_cluster, skip_counts)
