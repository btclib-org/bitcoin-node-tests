# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_createmultisig` spend half, on tf2's own harness: btcd.

`rpc_createmultisig_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_createmultisig_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_createmultisig_test import (
    combinerawtransaction_preconditions,
    every_multisig_spends_once_the_node_combines_its_signatures,
    sixteen_of_twenty_spends_once_the_node_combines_its_signatures,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_every_multisig_spends_once_the_node_combines_its_signatures(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    every_multisig_spends_once_the_node_combines_its_signatures(
        btcd_cluster, skip_counts
    )


def test_sixteen_of_twenty_spends_once_the_node_combines_its_signatures(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    sixteen_of_twenty_spends_once_the_node_combines_its_signatures(
        btcd_cluster, skip_counts
    )


def test_combinerawtransaction_preconditions(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    combinerawtransaction_preconditions(btcd_cluster, skip_counts, lambda _node: True)
