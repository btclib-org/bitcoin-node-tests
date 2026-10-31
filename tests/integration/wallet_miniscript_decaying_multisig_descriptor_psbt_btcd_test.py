# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `wallet_miniscript_decaying_multisig_descriptor_psbt`: btcd.

`wallet_miniscript_decaying_multisig_descriptor_psbt_test.py` beside
this module is the body, run here against btcd, a target rather than the
oracle (rule 3 of issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration \
        -k wallet_miniscript_decaying_multisig_descriptor_psbt_btcd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_miniscript_decaying_multisig_descriptor_psbt_test import (
    a_decaying_multisig_spends_with_fewer_signers_past_each_lock,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_decaying_multisig_spends_with_fewer_signers_past_each_lock(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_decaying_multisig_spends_with_fewer_signers_past_each_lock(
        btcd_cluster, skip_counts
    )
