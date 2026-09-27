# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, rewritten on tf2's own harness: btclib-node.

`p2p_invalid_messages_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `btclib-node`'s own `frame_message`
(`btclib_node/p2p/connection.py`) refuses both facts -- a wrong network
magic and a length over `MAX_PROTOCOL_MESSAGE_LENGTH` -- and
`Connection.run` stops the connection for either, on PyPI's `2026.9.24`
and on `main` alike: the wire half is the same fact on this node too, and
passes, for both tests here.

The log half is not: this node's own `Logger` (`log.py`) writes English,
not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and both log tests skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_invalid_messages_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_invalid_messages_test import (
    oversized_message_disconnects_the_peer,
    oversized_message_is_logged,
    wrong_magic_bytes_disconnects_the_peer,
    wrong_magic_bytes_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_wrong_magic_bytes_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    wrong_magic_bytes_disconnects_the_peer(btclib_node_adapter)


def test_wrong_magic_bytes_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    wrong_magic_bytes_is_logged(btclib_node_adapter, skip_counts)


def test_oversized_message_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    oversized_message_disconnects_the_peer(btclib_node_adapter)


def test_oversized_message_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_message_is_logged(btclib_node_adapter, skip_counts)
