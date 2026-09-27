# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""`fill_mempool`, on tf2's own harness: btclib-node.

`mempool_fill_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MAXMEMPOOL` is not declared:
measured against `cli.py`'s own `_OPTIONS` on `main`, `-maxmempool` is
not one of its registered flags -- a counted skip on that capability
alone, before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_fill_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_fill_test import (
    fill_mempool_evicts_its_own_low_fee_rate_transaction,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_fill_mempool_evicts_its_own_low_fee_rate_transaction(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    fill_mempool_evicts_its_own_low_fee_rate_transaction(
        btclib_node_cluster, skip_counts
    )
