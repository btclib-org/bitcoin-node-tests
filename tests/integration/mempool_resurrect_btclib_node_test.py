# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_resurrect`, rewritten on tf2's own harness: btclib-node.

`mempool_resurrect_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` is declared only by a build
that connects a submitted block with no peer (`btclib_node.py`'s own
docstring): PyPI's `2026.9.24` is a counted skip here, and a `main` from
btclib-node PR 1152 on runs the scenario.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_resurrect_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_resurrect_test import (
    a_reorg_returns_spent_coinbases_to_the_mempool,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_reorg_returns_spent_coinbases_to_the_mempool(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_reorg_returns_spent_coinbases_to_the_mempool(btclib_node_adapter, skip_counts)
