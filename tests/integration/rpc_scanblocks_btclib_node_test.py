# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_scanblocks`, rewritten on this harness: btclib-node.

The same requests `rpc_scanblocks_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.BLOCK_FILTER_INDEX` is not declared: measured against
`cli.py`'s registered options, `_build_parser` on the released build and
`_OPTIONS` on `main`, `-blockfilterindex` is not one of its registered
flags, and neither build's RPC dispatch answers `scanblocks` -- a
counted skip on that capability alone, before any node is ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_scanblocks_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_scanblocks_finds_the_blocks_paying_what_it_is_asked_for(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.BLOCK_FILTER_INDEX` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.BLOCK_FILTER_INDEX, BtclibNodeAdapter.capabilities, skip_counts)


def test_scanblocks_refuses_without_the_index(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.BLOCK_FILTER_INDEX` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.BLOCK_FILTER_INDEX, BtclibNodeAdapter.capabilities, skip_counts)
