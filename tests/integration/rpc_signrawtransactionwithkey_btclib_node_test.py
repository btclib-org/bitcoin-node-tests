# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_signrawtransactionwithkey`, on tf2's own harness: btclib-node.

`rpc_signrawtransactionwithkey_test.py` beside this module is the body,
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.SIGN_RAW_TRANSACTION` is not
declared (`btclib_node.py`'s own docstring is why), so each is a counted
skip, ahead of `Capability.MINE` where the body asks for it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/rpc_signrawtransactionwithkey_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_prevtxs_described_input_is_signed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_prevtxs_described_input_is_signed(btclib_node_cluster, skip_counts)


def test_a_witness_script_input_is_signed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_witness_script_input_is_signed(btclib_node_cluster, skip_counts)


def test_a_pay_to_anchor_input_is_signed_with_no_key(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_pay_to_anchor_input_is_signed_with_no_key(btclib_node_cluster, skip_counts)


def test_an_invalid_sighash_type_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_invalid_sighash_type_is_refused(btclib_node_cluster, skip_counts)


def test_an_invalid_private_key_or_transaction_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    an_invalid_private_key_or_transaction_is_refused(btclib_node_cluster, skip_counts)
