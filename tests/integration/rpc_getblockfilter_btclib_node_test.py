# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockfilter`, rewritten on tf2's own harness: btclib-node.

`rpc_getblockfilter_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.BLOCK_FILTER_INDEX` is not
declared: `cli.py` registers no `-blockfilterindex`, and
`getblockfilter` names no callback in `rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` and at `main` (`25776772`)
alike. So this is a counted skip before any node is restarted or mined
on.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_getblockfilter_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_getblockfilter_test import (
    getblockfilter_answers_for_active_and_stale_blocks,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_getblockfilter_answers_for_active_and_stale_blocks(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getblockfilter_answers_for_active_and_stale_blocks(btclib_node_cluster, skip_counts)
