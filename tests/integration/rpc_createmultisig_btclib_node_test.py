# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_createmultisig` spend half, on tf2's own harness: btclib-node.

`rpc_createmultisig_test.py` beside this module holds the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.SIGN_RAW_TRANSACTION` is not
declared (`btclib_node.py`'s own docstring is why), so each is a counted
skip ahead of `Capability.MINE`. Construction is
`rpc_createmultisig_bitcoind_test.py`'s alone, that module's own
docstring having why.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_createmultisig_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_every_multisig_spends_once_the_node_combines_its_signatures(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    every_multisig_spends_once_the_node_combines_its_signatures(
        btclib_node_cluster, skip_counts
    )


def test_sixteen_of_twenty_spends_once_the_node_combines_its_signatures(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sixteen_of_twenty_spends_once_the_node_combines_its_signatures(
        btclib_node_cluster, skip_counts
    )


def test_combinerawtransaction_preconditions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    combinerawtransaction_preconditions(
        btclib_node_cluster, skip_counts, lambda _node: True
    )
