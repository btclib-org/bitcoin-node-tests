# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_getdescriptoractivity`, on tf2's own harness: btclib-node.

The same requests `rpc_getdescriptoractivity_bitcoind_test.py` makes,
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DESCRIPTOR_ACTIVITY` is not
declared (`btclib_node.py`'s own docstring is why: `getdescriptoractivity`
names no callback in its dispatch table, on either build), so every
subject is a counted skip ahead of `Capability.MINE`, which the subjects
needing a `MiniWallet` also ask for.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/rpc_getdescriptoractivity_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_no_activity_for_an_unused_address(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    pytest.fail("not ported for this node")


def test_activity_in_block(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_no_mempool_inclusion(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    require(Capability.MINE, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_invalid_blockhash(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    pytest.fail("not ported for this node")


def test_invalid_descriptor(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    pytest.fail("not ported for this node")


def test_required_args(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the same request the bitcoind module makes."""
    require(
        Capability.DESCRIPTOR_ACTIVITY, btclib_node_adapter.capabilities, skip_counts
    )
    pytest.fail("not ported for this node")
