# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, rewritten on tf2's own harness: btclib-node.

`p2p_invalid_messages_bitcoind_test.py`'s own docstring is where the two
halves this splits `test_magic_bytes` and `test_size` into are argued.
`btclib-node`'s own `frame_message` (`btclib_node/p2p/connection.py`)
calls `btclib.p2p.Message.parse`, which raises a `BTClibValueError` for
either fact -- a wrong network magic or a payload over
`MAX_PROTOCOL_MESSAGE_LENGTH` -- and `Connection.run`'s own handler
(`connection.py`, "A `BTClibException` is `Message.parse` ... refusing
this peer's own envelope -- a bad checksum, an oversized length, a
message for another network") discourages the peer's address and stops
the connection for both alike: the wire half is the same fact on this
node too, so it is asked for, and passes, for both tests here.

The log half is not: this node's own `Logger` (`log.py`) writes English,
not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and both log tests skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_invalid_messages_btclib_node_test.py
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Message, Ping
from btclib.p2p.limits import MAX_PROTOCOL_MESSAGE_LENGTH
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_WRONG_MAGIC = bytes(byte ^ 0xFF for byte in _MAGIC)


def _oversized_message() -> bytes:
    """Return the same over-bound message the bitcoind module builds."""
    payload = b"a" * (MAX_PROTOCOL_MESSAGE_LENGTH + 1)
    message = Message(_MAGIC, "oversized", payload, check_validity=False)
    return message.serialize(check_validity=False)


def _send_oversized(peer: Peer) -> None:
    """Send `_oversized_message()`, tolerant of the node closing mid-send.

    `p2p_invalid_messages_bitcoind_test.py`'s own docstring is where this
    is measured: this node's own `Connection.run` closes the socket
    before this side has finished writing the payload, so `sendall`
    itself raises a `BrokenPipeError` here rather than only the
    following `receive`.
    """
    with contextlib.suppress(ConnectionError):
        peer.send_raw(_oversized_message())


def test_wrong_magic_bytes_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def test_wrong_magic_bytes_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_oversized_message_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        _send_oversized(peer)
        peer.wait_for_disconnect()


def test_oversized_message_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
