# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_datacarrier`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_datacarrier.py`:
`mempool_datacarrier_test.py` beside this module holds each body, run
here against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_datacarrier_test import (
    bare_multisig_is_permitted_by_default,
    datacarrier_disabled_refuses_any_null_data_output,
    datacarriersize_bounds_the_payload,
    default_settings_allow_a_large_op_return,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_default_settings_allow_a_large_op_return(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    default_settings_allow_a_large_op_return(bitcoind_cluster, skip_counts)


def test_datacarrier_disabled_refuses_any_null_data_output(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    datacarrier_disabled_refuses_any_null_data_output(bitcoind_cluster, skip_counts)


def test_datacarriersize_bounds_the_payload(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    datacarriersize_bounds_the_payload(bitcoind_cluster, skip_counts)


def test_bare_multisig_is_permitted_by_default(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    bare_multisig_is_permitted_by_default(bitcoind_cluster, skip_counts)
