# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_expiry`, rewritten on this harness: btclib-node.

`mempool_expiry_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). It is a counted skip on
`Capability.MEMPOOL_EXPIRY`, which `btclib_node.py`'s own docstring has
no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_expiry_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_expiry_test import (
    a_transaction_and_its_child_expire_together,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_transaction_and_its_child_expire_together(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_transaction_and_its_child_expire_together(btclib_node_cluster, skip_counts)
