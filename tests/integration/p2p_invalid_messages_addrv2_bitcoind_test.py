# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, three of its four `addrv2` checks: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_addrv2_empty`,
`test_addrv2_no_addresses` and `test_addrv2_too_long_address`, each
through the shared `test_addrv2`: an `addrv2` with a hand-built payload,
its own `serialize` overridden so the raw octets travel unchecked by
either side's own codec, over a `SenderOfAddrV2` -- Core's own peer that
waits for the node's `sendaddrv2` before sending anything, so a node not
yet announcing BIP155 support is never bombarded with a message it may
not recognise. This repository's own `Peer.handshake` already negotiates
`WTXID_RELAY_VERSION` (`70016`), the same floor `net_processing.cpp`
gates `SENDADDRV2` on (`Signal ADDRv2 support (BIP155)`), so the node has
already sent it by the time `handshake` returns, and no explicit wait is
needed to reach the same guarantee `SenderOfAddrV2` asks for by name.

None of Core's own four checks disconnects the peer -- an addrv2 that
fails to deserialize is one more entry `ProcessMessages`'s own outer
`catch` logs and moves past, `src/net_processing.cpp`'s comment on it
argued in `p2p_invalid_messages_dropped_bitcoind_test.py` -- so each is a
wire-and-log pair of the same shape that module already uses: a `ping`
round-trip confirms the connection is still there, and
`Capability.DEBUG_LOG` gates the log half.

`test_addrv2_unrecognized_network` is not ported: it needs bitcoind's own
`Added N addresses (of M) from ...` line, which is `LogDebug(BCLog::ADDRMAN,
...)` (`src/addrman.cpp`) rather than `BCLog::NET`, and this repository's
own `BitcoindAdapter._command` fixes `-debug=net` for the whole log family
rather than per test. The one `NET`-category line the same code path also
writes, `Received addr: N addresses (M processed, K rate-limited)`, names
a fact, but measured live over several runs it always answers `(1
processed, 1 rate-limited)` for the same two entries -- this
connection's own initial `peer.m_addr_token_bucket`, not a fact about an
unrecognized network or about `addrv2` at all. `TF2.md` names this row's
own gap.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Message, Ping, Pong
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")


def _addrv2_message(payload: bytes) -> bytes:
    """Return an `addrv2` message carrying `payload` unchecked."""
    message = Message(_MAGIC, "addrv2", payload, check_validity=False)
    return message.serialize(check_validity=False)


def _sync(peer: Peer) -> None:
    """Round-trip a `ping`, so an earlier send is known to be processed."""
    nonce = secrets.randbelow(2**64)
    peer.send(Ping(nonce))
    peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)


def test_addrv2_empty_keeps_the_connection(bitcoind_adapter: BitcoindAdapter) -> None:
    """The wire half: an empty `addrv2` is dropped, not disconnected."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(b""))
        _sync(peer)


def test_addrv2_empty_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for what it silently dropped."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            ["received: addrv2 (0 bytes)", "ProcessMessages(addrv2, 0 bytes)"],
        ),
    ):
        peer.handshake()
        peer.send_raw(_addrv2_message(b""))
        _sync(peer)


def test_addrv2_no_addresses_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a zero-entry `addrv2` needs no rewriting either."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(bytes.fromhex("00")))
        _sync(peer)


def test_addrv2_no_addresses_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own count of what it read and kept."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            [
                "received: addrv2 (1 bytes)",
                "Received addr: 0 addresses (0 processed, 0 rate-limited)",
            ],
        ),
    ):
        peer.handshake()
        peer.send_raw(_addrv2_message(bytes.fromhex("00")))
        _sync(peer)


# Core's own `test_addrv2_too_long_address`: one entry, a IPv4 network
# id claiming an address of 513 octets -- one more than `MAX_ADDRV2_SIZE`
# (`btclib.p2p.limits`, BIP155's own bound).
_TOO_LONG_ADDRESS = bytes.fromhex(
    "01"  # one entry
    "61bc6649"  # time
    "00"  # service flags, COMPACTSIZE(NODE_NONE)
    "01"  # network type (IPv4)
    "fd0102"  # address length, COMPACTSIZE(513)
    + "ab" * 513  # address
    + "208d"  # port
)


def test_addrv2_too_long_address_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: an over-bound address is dropped, not disconnected."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(_TOO_LONG_ADDRESS))
        _sync(peer)


def test_addrv2_too_long_address_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for what it silently dropped."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            [
                "received: addrv2 (525 bytes)",
                "ProcessMessages(addrv2, 525 bytes)",
                "Address too long: 513 > 512",
            ],
        ),
    ):
        peer.handshake()
        peer.send_raw(_addrv2_message(_TOO_LONG_ADDRESS))
        _sync(peer)
