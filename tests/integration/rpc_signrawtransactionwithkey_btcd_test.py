# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_signrawtransactionwithkey`, on tf2's own harness: btcd.

`rpc_signrawtransactionwithkey_test.py` beside this module is the body,
run here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_signrawtransactionwithkey_btcd_test.py
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

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_prevtxs_described_input_is_signed(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_prevtxs_described_input_is_signed(btcd_cluster, skip_counts)


def test_a_witness_script_input_is_signed(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_witness_script_input_is_signed(btcd_cluster, skip_counts)


def test_a_pay_to_anchor_input_is_signed_with_no_key(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_pay_to_anchor_input_is_signed_with_no_key(btcd_cluster, skip_counts)


def test_an_invalid_sighash_type_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_invalid_sighash_type_is_refused(btcd_cluster, skip_counts)


def test_an_invalid_private_key_or_transaction_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    an_invalid_private_key_or_transaction_is_refused(btcd_cluster, skip_counts)
