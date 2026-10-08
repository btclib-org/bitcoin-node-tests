# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, three checks it drops, over either node.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_duplicate_version_msg`,
`test_checksum` and `test_msgtype` (its non-v2 branch, this repository's
own `Peer` speaking no other): `p2p_invalid_messages_test.py`'s own
docstring is where the other shape, a header `V1Transport::readHeader`
refuses outright, is argued -- these three instead reach
`V1Transport::GetReceivedMessage` (`src/net.cpp`), which sets
`reject_message` rather than returning early, and
`CNode::ReceiveMsgBytes`'s own comment is explicit about what that buys:
"Message deserialization failed. Drop the message but don't disconnect
the peer." Each is a wire-and-log pair after all, the wire fact being the
opposite one from the other module: the connection *stays open*, checked
by round-tripping a `ping` afterwards rather than by
`wait_for_disconnect`.

Two of the three corrupt a well-formed `ping` in place, byte for byte the
way Core's own `test_checksum`/`test_msgtype` do (`msg[:cut] +
replacement + msg[cut + n:]`), rather than building a payload of their
own: what each is about is a header field, not `ping`'s own body, so any
serialized message supplies one. `duplicate_version_keeps_the_connection`
sends a second, ordinary `Version` after `handshake` has completed the
first exchange -- `net_processing.cpp`'s own guard is `pfrom.nVersion !=
0`, true from that point on, so no corruption is needed to reach it.

Core's own `test_checksum` and `test_msgtype` also check
`getpeerinfo()['bytesrecv_per_msg']['*other*']` to confirm the dropped
message's bytes were still counted; this narrows to the log assertion
alone, that byte count being a smaller and separate claim about traffic
accounting rather than about the drop itself.

`p2p_invalid_messages_dropped_bitcoind_test.py` and
`p2p_invalid_messages_dropped_btclib_node_test.py` run every body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import Ping, Pong, Version

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "debug_log",
    "duplicate_version_is_logged",
    "duplicate_version_keeps_the_connection",
    "invalid_msgtype_is_logged",
    "invalid_msgtype_keeps_the_connection",
    "sync",
    "wrong_checksum_is_logged",
    "wrong_checksum_keeps_the_connection",
]

_MAGIC = magic_from_chain("regtest")
# magic (4) + command (12) + length (4): the checksum's own offset in a
# serialized message, `CMessageHeader`'s own layout (`src/protocol.h`).
_CHECKSUM_AT = 4 + 12 + 4


def _wrong_checksum_message() -> bytes:
    """Return a well-framed `ping`, its own checksum overwritten."""
    raw = Ping(0).to_message(_MAGIC).serialize()
    return raw[:_CHECKSUM_AT] + b"\xff\xff\xff\xff" + raw[_CHECKSUM_AT + 4 :]


def _invalid_msgtype_message() -> bytes:
    """Return a well-framed `ping`, one interior command byte zeroed.

    `p`, `i` kept, the third byte of the 12-byte command overwritten with
    a NUL ahead of a fourth (`g`) that stays non-NUL:
    `CMessageHeader::IsMessageTypeValid` (`src/protocol.cpp`) requires
    every byte after the first NUL to be NUL too, and this breaks exactly
    that, the same shape Core's own test builds by hand.
    """
    raw = Ping(0).to_message(_MAGIC).serialize()
    command_at = 4 + 2  # magic, then the third byte of the command field
    return raw[:command_at] + b"\x00" + raw[command_at + 1 :]


def sync(peer: Peer) -> None:
    """Round-trip a `ping`, so an earlier send is known to be processed.

    Raises whatever `Peer.wait_for` raises if the connection closed
    instead of answering -- the wire half's own assertion, for a fact
    whose whole content is "this connection is still usable".
    """
    nonce = secrets.randbelow(2**64)
    peer.send(Ping(nonce))
    peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)


def debug_log(
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


def duplicate_version_keeps_the_connection(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a second `version` is dropped, not disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Version())
        sync(peer)


def duplicate_version_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for what it silently dropped.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    log_path = debug_log(adapter, skip_counts)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(log_path, ["redundant version message"]),
    ):
        peer.handshake()
        peer.send(Version())
        sync(peer)


def wrong_checksum_keeps_the_connection(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a bad checksum is dropped, not disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_wrong_checksum_message())
        sync(peer)


def wrong_checksum_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for what it silently dropped.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    log_path = debug_log(adapter, skip_counts)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(log_path, ["Header error: Wrong checksum"]),
    ):
        peer.handshake()
        peer.send_raw(_wrong_checksum_message())
        sync(peer)


def invalid_msgtype_keeps_the_connection(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: an invalid message type is dropped, not fatal.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_invalid_msgtype_message())
        sync(peer)


def invalid_msgtype_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for what it silently dropped.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    log_path = debug_log(adapter, skip_counts)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(log_path, ["Header error: Invalid message type"]),
    ):
        peer.handshake()
        peer.send_raw(_invalid_msgtype_message())
        sync(peer)
