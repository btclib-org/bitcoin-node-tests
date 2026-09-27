# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_net_deadlock`, rewritten on tf2's own harness: btclib-node.

`p2p_net_deadlock_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.RAW_MESSAGE` is not declared by
`BtclibNodeAdapter`: `sendmsgtopeer` names no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, on the released
build or on `main`, so this skips once its two nodes are started, before
either is asked to send anything.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_net_deadlock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_net_deadlock_test import (
    simultaneous_large_messages_do_not_deadlock,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_simultaneous_large_messages_do_not_deadlock(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    simultaneous_large_messages_do_not_deadlock(btclib_node_cluster, skip_counts)
