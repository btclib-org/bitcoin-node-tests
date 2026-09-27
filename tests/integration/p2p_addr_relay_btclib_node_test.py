# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addr_relay`, rewritten on tf2's own harness: btclib-node.

`p2p_addr_relay_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
The wire half passes on PyPI's `2026.9.24` and on `main`, by two paths:
the released build's `callbacks.addr` calls btclib's own `Addr.parse`,
which refuses a count past `MAX_ADDR_TO_SEND`, and `handle_p2p`
(`p2p/main.py`) discourages and stops the peer for it; `main` raises a
`MisbehavingError` ahead of the parse, which `_drop` hands to
`maybe_discourage_and_disconnect`. The log half is a counted skip on
every build, `Capability.DEBUG_LOG` being bitcoind's alone.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_addr_relay_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_addr_relay_test import (
    oversized_addr_disconnects_the_peer,
    oversized_addr_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_addr_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half this module's docstring names."""
    oversized_addr_disconnects_the_peer(btclib_node_adapter)


def test_oversized_addr_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_addr_is_logged(btclib_node_adapter, skip_counts)
