# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getdata`, rewritten on tf2's own harness: btclib-node.

`p2p_getdata_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
A build with the defect of
[ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)
fails it: `block_db` never stores genesis, so it cannot serve the block
this test asks for.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_getdata_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_getdata_test import (
    invalid_getdata_does_not_stop_a_later_valid_one,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter

pytestmark = pytest.mark.integration


def test_invalid_getdata_does_not_stop_a_later_valid_one(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the invalid item first, the valid one still served."""
    invalid_getdata_does_not_stop_a_later_valid_one(btclib_node_adapter)
