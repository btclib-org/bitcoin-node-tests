# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_spend_coinbase`, on tf2's own harness: btclib-node.

The same request `mempool_spend_coinbase_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` is not declared
(`btclib_node.py`'s own docstring is why: a solo node never leaves
`NodeStatus.SyncingHeaders`, ISS btclib-node#1071), so this is a counted
skip rather than a run.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_spend_coinbase_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_mature_coinbase_spends_and_an_immature_one_is_refused(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
