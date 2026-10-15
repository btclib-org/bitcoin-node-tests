# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_nobloomfilter_messages`, its filtered-block step: btclib-node.

`p2p_nobloomfilter_messages_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The log half skips: this node does not declare
`Capability.DEBUG_LOG` (`btclib_node.py`'s own `capabilities`).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_nobloomfilter_messages_test import (
    filtered_block_request_disconnects_the_peer,
    filtered_block_request_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_filtered_block_request_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    filtered_block_request_disconnects_the_peer(btclib_node_adapter)


def test_filtered_block_request_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    filtered_block_request_is_logged(btclib_node_adapter, skip_counts)
