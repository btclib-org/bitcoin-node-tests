# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_net_deadlock`, rewritten on tf2's own harness: btclib-node.

The same request `p2p_net_deadlock_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.RAW_MESSAGE` is not declared by `BtclibNodeAdapter`: it has
no `sendmsgtopeer` equivalent in its RPC dispatch table at all, measured
against `382a29fb`'s `src/btclib_node/rpc/callbacks.py`, so this skips
before either capability is asked to do anything.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_net_deadlock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_simultaneous_large_messages_do_not_deadlock(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.RAW_MESSAGE, btclib_node_adapter.capabilities, skip_counts)
