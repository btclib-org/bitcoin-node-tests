# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, three checks it drops instead: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_duplicate_version_msg`,
`test_checksum` and `test_msgtype` (its non-v2 branch, this repository's
own `Peer` speaking no other): `p2p_invalid_messages_bitcoind_test.py`'s
own docstring is where the other shape, a header `V1Transport::readHeader`
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
serialized message supplies one. `test_duplicate_version_keeps_the_connection`
sends a second, ordinary `Version` after `handshake` has completed the
first exchange -- `net_processing.cpp`'s own guard is `pfrom.nVersion !=
0`, true from that point on, so no corruption is needed to reach it.

Core's own `test_checksum` and `test_msgtype` also check
`getpeerinfo()['bytesrecv_per_msg']['*other*']` to confirm the dropped
message's bytes were still counted; this narrows to the log assertion
alone, that byte count being a smaller and separate claim about traffic
accounting rather than about the drop itself.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Ping, Pong, Version
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

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


def _sync(peer: Peer) -> None:
    """Round-trip a `ping`, so an earlier send is known to be processed.

    Raises whatever `Peer.wait_for` raises if the connection closed
    instead of answering -- the wire half's own assertion, for a fact
    whose whole content is "this connection is still usable".
    """
    nonce = secrets.randbelow(2**64)
    peer.send(Ping(nonce))
    peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)


def test_duplicate_version_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a second `version` is dropped, not disconnected."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Version())
        _sync(peer)


def test_duplicate_version_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for what it silently dropped."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["redundant version message"]
        ),
    ):
        peer.handshake()
        peer.send(Version())
        _sync(peer)


def test_wrong_checksum_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a bad checksum is dropped, not disconnected."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_wrong_checksum_message())
        _sync(peer)


def test_wrong_checksum_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for what it silently dropped."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["Header error: Wrong checksum"]
        ),
    ):
        peer.handshake()
        peer.send_raw(_wrong_checksum_message())
        _sync(peer)


def test_invalid_msgtype_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: an invalid message type is dropped, not disconnected."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_invalid_msgtype_message())
        _sync(peer)


def test_invalid_msgtype_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for what it silently dropped."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["Header error: Invalid message type"]
        ),
    ):
        peer.handshake()
        peer.send_raw(_invalid_msgtype_message())
        _sync(peer)
