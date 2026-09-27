# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_signrawtransactionwithkey`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/rpc_signrawtransactionwithkey.py`:
`rpc_signrawtransactionwithkey_test.py` beside this module is the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_signrawtransactionwithkey_test import (
    a_pay_to_anchor_input_is_signed_with_no_key,
    a_prevtxs_described_input_is_signed,
    a_witness_script_input_is_signed,
    an_invalid_private_key_or_transaction_is_refused,
    an_invalid_sighash_type_is_refused,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_prevtxs_described_input_is_signed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_prevtxs_described_input_is_signed(bitcoind_cluster, skip_counts)


def test_a_witness_script_input_is_signed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_witness_script_input_is_signed(bitcoind_cluster, skip_counts)


def test_a_pay_to_anchor_input_is_signed_with_no_key(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_pay_to_anchor_input_is_signed_with_no_key(bitcoind_cluster, skip_counts)


def test_an_invalid_sighash_type_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_invalid_sighash_type_is_refused(bitcoind_cluster, skip_counts)


def test_an_invalid_private_key_or_transaction_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    an_invalid_private_key_or_transaction_is_refused(bitcoind_cluster, skip_counts)
