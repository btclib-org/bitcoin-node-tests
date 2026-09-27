# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_uptime`, rewritten on this repository's own harness: bitcoind.

Read from Core's `test/functional/rpc_uptime.py`: `rpc_uptime_test.py`
beside this module is the body, run here against bitcoind, which
declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_uptime_test import uptime_does_not_jump_with_the_wall_clock

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_uptime_does_not_jump_with_the_wall_clock(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    uptime_does_not_jump_with_the_wall_clock(bitcoind_adapter, skip_counts)
