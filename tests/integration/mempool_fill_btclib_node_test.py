# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""`fill_mempool`, on tf2's own harness: btclib-node.

The same request `mempool_fill_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.MAXMEMPOOL` is not declared: measured against `cli.py`'s
own `_OPTIONS` on `main`, `-maxmempool` is not one of its registered
flags -- a counted skip on that capability alone, before any node is
ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_fill_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_fill_mempool_evicts_its_own_low_fee_rate_transaction(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.MAXMEMPOOL` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.MAXMEMPOOL, BtclibNodeAdapter.capabilities, skip_counts)
