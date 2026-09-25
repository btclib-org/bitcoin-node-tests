# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_uptime`, rewritten on this repository's own harness: bitcoind.

Read from Core's `test/functional/rpc_uptime.py` (`406c2348ddbf`,
2026-06-13) rather than ported: that file drives a `TestNode` over
Core's own harness and reads `time.sleep`/`uptime`/`setmocktime` as
`TestNode` attributes. This rewrites the same subject over `NodeAdapter`
(rule 5 of issue btclib-org/btclib#2220: tf2's own adapter). No
deviation from Core's own claim: a single clean-chain node, `uptime`
before and after `Capability.CLOCK` (`capability.py`) jumps the clock
forward, is the whole of what either file asks.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_WAIT_TIME = 20_000


def test_uptime_does_not_jump_with_the_wall_clock(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject: `uptime` tracks the mock clock, not the real one."""
    require(Capability.CLOCK, bitcoind_adapter.capabilities, skip_counts)
    time.sleep(1)  # let some real time pass before the first reading
    uptime_before = bitcoind_adapter.rpc.call("uptime")
    assert isinstance(uptime_before, int)
    assert uptime_before > 0

    bitcoind_adapter.set_mock_time(int(time.time()) + _WAIT_TIME)
    try:
        uptime_after = bitcoind_adapter.rpc.call("uptime")
    finally:
        bitcoind_adapter.set_mock_time(0)  # released even where the call above raises
    assert isinstance(uptime_after, int)
    assert uptime_after - uptime_before < _WAIT_TIME
