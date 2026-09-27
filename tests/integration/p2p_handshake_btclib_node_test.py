# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`, rewritten on tf2's own harness: btclib-node.

`p2p_handshake_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
The wire half fails on PyPI's `2026.9.24`: `handle_p2p_handshake`
(`p2p/main.py`) discourages and stops a `verack` arriving once the
connection is already `Connected`
([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)).
A `main` past that issue ignores it, as Core does. The log half is a counted
skip on every build, `Capability.DEBUG_LOG` being bitcoind's alone.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_handshake_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_handshake_test import (
    redundant_verack_is_logged,
    redundant_verack_keeps_the_connection,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_redundant_verack_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build (ISS btclib-node#1133)."""
    redundant_verack_keeps_the_connection(btclib_node_adapter)


def test_redundant_verack_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    redundant_verack_is_logged(btclib_node_adapter, skip_counts)
