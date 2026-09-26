# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, its four `addrv2` checks: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_addrv2_empty`,
`test_addrv2_no_addresses`, `test_addrv2_too_long_address` and
`test_addrv2_unrecognized_network`, each through the shared
`test_addrv2`: an `addrv2` with a hand-built payload, its own
`serialize` overridden so the raw octets travel unchecked by either
side's own codec, over a `SenderOfAddrV2` -- Core's own peer that
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

`test_addrv2_unrecognized_network`'s two log lines past the first,
`9.9.9.9:8333` and `Added 1 addresses`, are `LogDebug(BCLog::ADDRMAN,
...)`'s (`src/addrman.cpp`), which `BitcoindAdapter._command`'s own
`-debug=addrman` enables. Its node is started for it, with two settings
Core's own run of this file has and `bitcoind_adapter` does not.
`-whitelist=addr@127.0.0.1` is `InvalidMessagesTest.set_test_params`'s
own: without `NetPermissionFlags::Addr`, `net_processing.cpp`'s own
address-rate limiter processes one of the two entries and defers the
other, and `std::shuffle` picks which, so `9.9.9.9` is added on some
runs and not on others. `-connect=0` is what Core's own `write_config`
(`test_framework/util.py`) gives every node, and what keeps
`CConnman::Start` (`src/net.cpp`) from starting `ThreadOpenConnections`:
measured against the pinned `31.1` without it, once `9.9.9.9` is in the
address manager that thread selects it over and over, each selection
one more `addrman` line in the log. The wire half starts one of these
nodes too rather than using `bitcoind_adapter`, which a session shares:
left holding the address, that node would write those lines for the
rest of the session.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Message, Ping, Pong
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import free_ports
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

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


@contextmanager
def _addr_node(
    make_adapter: AdapterFactory, bitcoind_path: str, datadir: Path
) -> Iterator[BitcoindAdapter]:
    """Yield a started node exempt from address-rate limiting, never dialling.

    The module docstring is why each of the two flags is here.
    """
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        datadir,
        rpc_port,
        p2p_port,
        extra_args=("-whitelist=addr@127.0.0.1", "-connect=0"),
    )
    adapter.start()
    try:
        yield adapter
    finally:
        adapter.stop()


def _unrecognized_network() -> bytes:
    """Return Core's own `test_addrv2_unrecognized_network` payload.

    Two entries stamped with the current time: an unrecognized network id,
    to be ignored without impeding the next entry, and `9.9.9.9:8333`,
    to be added.
    """
    now = int(time.time()).to_bytes(4, "little").hex()
    return bytes.fromhex(
        "02"  # two entries
        + now  # time
        + "01"  # service flags, COMPACTSIZE(NODE_NETWORK)
        + "99"  # network type (unrecognized)
        + "02"  # address length, COMPACTSIZE(2)
        + "ab" * 2  # address
        + "208d"  # port
        + now  # time
        + "01"  # service flags, COMPACTSIZE(NODE_NETWORK)
        + "01"  # network type (IPv4)
        + "04"  # address length, COMPACTSIZE(4)
        + "09" * 4  # address
        + "208d"  # port
    )


def test_addrv2_unrecognized_network_keeps_the_connection(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """The wire half: an entry of an unknown network is ignored, not fatal."""
    with (
        _addr_node(make_adapter, bitcoind_path, tmp_path) as node,
        Peer(node.p2p_address, _MAGIC) as peer,
    ):
        peer.handshake()
        peer.send_raw(_addrv2_message(_unrecognized_network()))
        _sync(peer)


def test_addrv2_unrecognized_network_is_logged(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The log half: the entry after the unrecognized one is still added."""
    with _addr_node(make_adapter, bitcoind_path, tmp_path) as node:
        require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
        with (
            Peer(node.p2p_address, _MAGIC) as peer,
            assert_debug_log(
                node.debug_log_path,
                ["received: addrv2 (25 bytes)", "9.9.9.9:8333", "Added 1 addresses"],
            ),
        ):
            peer.handshake()
            peer.send_raw(_addrv2_message(_unrecognized_network()))
            _sync(peer)
