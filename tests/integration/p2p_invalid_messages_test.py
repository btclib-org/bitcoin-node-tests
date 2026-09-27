# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, its two header refusals, over either node.

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

`wrong_magic_bytes_disconnects_the_peer` and
`oversized_message_disconnects_the_peer` read the wire: a disconnect is
`getpeerinfo`'s or, cheaper here, `Peer.receive`'s own `ConnectionError`, so no
capability is asked for. `_oversized_message`'s payload, like the one Core's own
`test_size` builds, is one octet over `MAX_PROTOCOL_MESSAGE_LENGTH`
(`btclib.p2p.limits`), the same bound Core's own `hdr.nMessageSize >
MAX_PROTOCOL_MESSAGE_LENGTH` reads, built with `check_validity=False`:
`Message.assert_valid` refuses to construct the very octets this header error is
about.

`wrong_magic_bytes_is_logged` and `oversized_message_is_logged`
are the half nothing but a log carries: Core's own wording, `Header
error: Wrong MessageStart ... received` and `Header error: Size too
large (..., N bytes)` (`src/net.cpp`), is bitcoind's own sentence, not a
fact of the protocol itself, so each asks for `Capability.DEBUG_LOG` and
is where a node lacking it skips rather than being asked to spell an
English sentence Core never asked it to write.

`_send_oversized` sends `_oversized_message()`'s own several-megabyte
payload and swallows the `ConnectionError` a node's disconnect can raise
on the send itself. Measured live against bitcoind, `readHeader` acts on
the header alone and `CNode::ReceiveMsgBytes` (`src/net.cpp`) closes the
socket before this connection has finished writing the rest of the
payload, so `socket.sendall` itself raises rather than only the
following `receive`; a node that closes only after reading the payload
raises nothing there, and the suppression changes nothing for it.
`wait_for_disconnect` afterwards is unaffected --
the connection is already gone either way -- and is what the wire half
still asks for, rather than reading the raised exception as the fact
under test.

`p2p_invalid_messages_bitcoind_test.py` and
`p2p_invalid_messages_btclib_node_test.py` run every body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from btclib.p2p import Message, Ping
from btclib.p2p.limits import MAX_PROTOCOL_MESSAGE_LENGTH
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "oversized_message_disconnects_the_peer",
    "oversized_message_is_logged",
    "wrong_magic_bytes_disconnects_the_peer",
    "wrong_magic_bytes_is_logged",
]

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


def _debug_log(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> Path:
    """Return the log a log half reads, or skip where the node keeps none.

    :raises TypeError: `adapter` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
    if not isinstance(adapter, BitcoindAdapter):
        err_msg = f"{type(adapter).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return adapter.debug_log_path


def wrong_magic_bytes_disconnects_the_peer(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a message on the wrong network drops the peer.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def wrong_magic_bytes_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for why it disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    log_path = _debug_log(adapter, skip_counts)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(log_path, ["Header error: Wrong MessageStart"]),
    ):
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def oversized_message_disconnects_the_peer(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a header over the protocol's bound drops the peer.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        _send_oversized(peer)
        peer.wait_for_disconnect()


def oversized_message_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for why it disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    log_path = _debug_log(adapter, skip_counts)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(log_path, ["Header error: Size too large"]),
    ):
        peer.handshake()
        _send_oversized(peer)
        peer.wait_for_disconnect()
