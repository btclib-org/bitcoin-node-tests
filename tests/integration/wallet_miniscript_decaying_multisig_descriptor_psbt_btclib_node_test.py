# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `wallet_miniscript_decaying_multisig_descriptor_psbt`: btclib-node.

`wallet_miniscript_decaying_multisig_descriptor_psbt_test.py` beside this
module holds the body, run here on tf2's own harness against the target
rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.NODE_WALLET` is not declared: btclib-node keeps no wallet
(`btclib_node.py`'s own docstring), and a wallet kept beside it is
[ISS 199](https://github.com/btclib-org/bitcoin-node-tests/issues/199)'s
to reach -- a counted skip on that capability, asked for first.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration \
        -k wallet_miniscript_decaying_multisig_descriptor_psbt_btclib_node
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_miniscript_decaying_multisig_descriptor_psbt_test import (
    a_decaying_multisig_spends_with_fewer_signers_past_each_lock,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_decaying_multisig_spends_with_fewer_signers_past_each_lock(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_decaying_multisig_spends_with_fewer_signers_past_each_lock(
        btclib_node_cluster, skip_counts
    )
