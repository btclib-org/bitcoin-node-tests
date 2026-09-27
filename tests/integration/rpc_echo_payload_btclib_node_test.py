# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_echo_payload`, rewritten on this harness: btclib-node.

The same claim `rpc_echo_payload_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.RPC_WORK_QUEUE` is not declared (`btclib_node.py`'s own
docstring has the measurement), so this counts a skip before any node
is spawned. A port for this node also needs `echo`, which
`rpc/callbacks.py`'s own dispatch table does not name, and accepts a
refusal in this node's own terms rather than bitcoind's HTTP 503.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_echo_payload_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_payload_is_answered_or_refused_never_left_to_time_out(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.RPC_WORK_QUEUE` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.RPC_WORK_QUEUE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
