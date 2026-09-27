# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_uptime`, rewritten on tf2's own harness: btclib-node.

`rpc_uptime_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.CLOCK` is not declared
(`btclib_node.py`'s own docstring is why: `setmocktime` names no
callback in `btclib-node`'s own RPC dispatch table), so this is a
counted skip rather than a run.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_uptime_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_uptime_test import uptime_does_not_jump_with_the_wall_clock

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_uptime_does_not_jump_with_the_wall_clock(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    uptime_does_not_jump_with_the_wall_clock(btclib_node_adapter, skip_counts)
