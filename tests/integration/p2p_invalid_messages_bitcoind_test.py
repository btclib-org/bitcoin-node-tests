# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_magic_bytes` and `test_size`
rather than ported whole: `InvalidMessagesTest` runs several methods in
sequence over one node, most needing `-whitelist=addr@127.0.0.1`
(family 3, this step's own next one) or a mined chain
(`Capability.MINE`, declared but not what either subject here needs).
This rewrites the two of them that share one shape -- both are
`V1Transport::readHeader` (`src/net.cpp`) refusing the header before a
message is ever handed to `GetReceivedMessage`, `return -1` in each
branch, which is what schedules the disconnect neither of Core's own two
tests has to ask for by name -- and stands in a module of its own rather
than joining `p2p_getdata`'s: Core's own test asserts two facts of one
action -- a malformed header gets its sender disconnected, and the
reason lands in the log -- and the log family's own rule (issue #5) is
that these two are ported differently.

`test_wrong_magic_bytes_disconnects_the_peer` and
`test_oversized_message_disconnects_the_peer` read the wire: a disconnect
is `getpeerinfo`'s or, cheaper here, `Peer.receive`'s own
`ConnectionError`, so no capability is asked for and both run -- and
pass -- on every node this step drives. `test_oversized_message`'s own
payload is one octet over `MAX_PROTOCOL_MESSAGE_LENGTH`
(`btclib.p2p.limits`), the same bound Core's own `hdr.nMessageSize >
MAX_PROTOCOL_MESSAGE_LENGTH` reads, built with `check_validity=False`:
`Message.assert_valid` refuses to construct the very octets this header
error is about.

`test_wrong_magic_bytes_is_logged` and `test_oversized_message_is_logged`
are the half nothing but a log carries: Core's own wording, `Header
error: Wrong MessageStart ... received` and `Header error: Size too
large (..., N bytes)` (`src/net.cpp`), is bitcoind's own sentence, not a
fact of the protocol itself, so each asks for `Capability.DEBUG_LOG` and
is where a node lacking it skips rather than being asked to spell an
English sentence Core never asked it to write.

`_send_oversized` sends `_oversized_message()`'s own several-megabyte
payload and swallows the `ConnectionError` this node's own disconnect
raises on the send itself: measured live, `readHeader` acts on the
header alone and `CNode::ReceiveMsgBytes` (`src/net.cpp`) closes the
socket before this connection has finished writing the rest of the
payload, so `socket.sendall` itself raises rather than only the
following `receive`. `wait_for_disconnect` afterwards is unaffected --
the connection is already gone either way -- and is what the wire half
still asks for, rather than reading the raised exception as the fact
under test.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Message, Ping
from btclib.p2p.limits import MAX_PROTOCOL_MESSAGE_LENGTH
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_WRONG_MAGIC = bytes(byte ^ 0xFF for byte in _MAGIC)


def _oversized_message() -> bytes:
    """Return a well-framed message one octet over the protocol's own bound.

    `check_validity=False` on construction and on `serialize` both: the
    length this builds is exactly the one `Message.assert_valid` and
    `Message.parse` alike exist to refuse, so asking either to check it
    would refuse building the very octets the wire is about to see.
    """
    payload = b"a" * (MAX_PROTOCOL_MESSAGE_LENGTH + 1)
    message = Message(_MAGIC, "oversized", payload, check_validity=False)
    return message.serialize(check_validity=False)


def _send_oversized(peer: Peer) -> None:
    """Send `_oversized_message()`, tolerant of the node closing mid-send."""
    with contextlib.suppress(ConnectionError):
        peer.send_raw(_oversized_message())


def test_wrong_magic_bytes_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a message on the wrong network gets the peer dropped."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def test_wrong_magic_bytes_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["Header error: Wrong MessageStart"]
        ),
    ):
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def test_oversized_message_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a header over the protocol's own bound drops the peer."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        _send_oversized(peer)
        peer.wait_for_disconnect()


def test_oversized_message_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["Header error: Size too large"]
        ),
    ):
        peer.handshake()
        _send_oversized(peer)
        peer.wait_for_disconnect()
