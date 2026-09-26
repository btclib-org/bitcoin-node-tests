# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_leak_tx`, on tf2's own harness: btclib-node.

The same requests `p2p_leak_tx_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each subject asks for `Capability.CLOCK` first,
the order the bitcoind module asks in, and then for `Capability.MINE`.
`Capability.CLOCK` is not declared (`btclib_node.py`'s own docstring is
why), so each of these is a counted skip on it rather than a run.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_leak_tx_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_tx_in_block(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.CLOCK, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_notfound_on_replaced_tx(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.CLOCK, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_notfound_on_unannounced_tx(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(Capability.CLOCK, btclib_node_adapter.capabilities, skip_counts)
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
