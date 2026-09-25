# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, four more of its own checks: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_oversized_inv_msg`,
`test_oversized_getdata_msg`, `test_oversized_headers_msg` (each through
the shared `test_oversized_msg`) and `test_invalid_pow_headers_msg`, none
ported by `p2p_invalid_messages_bitcoind_test.py`: that module's own
docstring already narrowed to `test_magic_bytes` alone, and its own
`InvalidMessagesTest.run_test` runs every one of these on the same node,
started once with `self.extra_args = [["-whitelist=addr@127.0.0.1"]]`.
That permission (`net_permissions.cpp`, `v31.1`'s `TryParsePermissionFlags`:
the string before `@` is parsed as a permission list, and `addr` is one)
grants `NetPermissionFlags::Addr` alone, not `NoBan` -- so it does not
exempt this connection from the discourage-and-disconnect
`net_processing.cpp`'s own `Misbehaving` schedules
(`PeerManagerImpl::MaybeDiscourageAndDisconnect`, `if
(pnode.HasPermission(NetPermissionFlags::NoBan)) { ... never disconnect
... }`), which is what the four checks below are about; dropping it is
the same narrowing `test_magic_bytes` already made.

Each of Core's own four calls `assert_debug_log(['Misbehaving', ...])`
around an oversized or PoW-invalid message and then waits for a
disconnect: two facts of one action, so each gets a wire half and a log
half of its own, the log family's own rule (issue #5). The wire half
needs nothing this step does not already give every node under test; the
log half is bitcoind's own wording for *why*, `Capability.DEBUG_LOG`
gating it as `p2p_invalid_messages_bitcoind_test.py`'s own two tests
already do.

Core's own `nCount`/`vInv.size()` check runs before any of the
message's own bytes past the count are read
(`net_processing.cpp`'s own `HEADERS`, `INV` and `GETDATA` branches, each
`Misbehaving` and `return` before touching an element), so the entries
themselves carry no claim beyond their own count and their own valid
framing -- `Inventory()`'s defaults for `inv`/`getdata`, and one
genesis-derived `BlockHeader` repeated for `headers`.

`test_invalid_pow_header_*` drops Core's own preliminary "send a valid
header first" step: `PeerManagerImpl::CheckHeadersPoW`
(`net_processing.cpp`) runs unconditionally at the top of
`ProcessHeadersMessage`, before any chain-state read, so a single
invalid-PoW header extending genesis reaches the same `Misbehaving` call
with no prior exchange needed. The invalid header is genesis's own
`bits` -- regtest's own trivial target, `0x207fffff` -- with a nonce
searched until the header's own displayed hash starts with `f`, Core's
own test's criterion and, under `0x207fffff`'s target (whose own top
byte is `0x7f`), sufficient on its own: any hash Core's own
`CheckProofOfWork` would refuse for exceeding this target.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from btclib.block import genesis_block
from btclib.block.block_header import BlockHeader
from btclib.p2p import GetData, Headers, Inv, Inventory
from btclib.p2p.limits import MAX_HEADERS_RESULTS, MAX_INV_SZ
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_GENESIS_HEADER = genesis_block("regtest").header


def _oversized_inv() -> Inv:
    """Return an `inv` one entry over `MAX_INV_SZ`, unchecked at build time."""
    return Inv([Inventory()] * (MAX_INV_SZ + 1), check_validity=False)


def _oversized_getdata() -> GetData:
    """Return a `getdata` one over `MAX_INV_SZ`, unchecked at build time."""
    return GetData([Inventory()] * (MAX_INV_SZ + 1), check_validity=False)


def _oversized_headers() -> Headers:
    """Return a `headers` one entry over `MAX_HEADERS_RESULTS`, unchecked."""
    return Headers([_GENESIS_HEADER] * (MAX_HEADERS_RESULTS + 1), check_validity=False)


def _invalid_pow_header() -> BlockHeader:
    """Return a header extending genesis whose own hash fails its target.

    Genesis's own `bits`, so the target is the one `CheckProofOfWork`
    holds this header to; the nonce is the first for which the header's
    own displayed hash starts with `f`, Core's own test's search and,
    under regtest's `0x207fffff` (target's own top byte `0x7f`),
    sufficient by itself: no hash starting `f` can be at or under it.
    """
    nonce = 0
    while True:
        header = BlockHeader(
            1,
            _GENESIS_HEADER.hash,
            bytes(32),
            datetime.now(UTC),
            _GENESIS_HEADER.bits,
            nonce,
            check_validity=False,
        )
        if header.hash[0] >= 0xF0:
            return header
        nonce += 1


def test_oversized_inv_disconnects_the_peer(bitcoind_adapter: BitcoindAdapter) -> None:
    """The wire half: an `inv` over `MAX_INV_SZ` gets the peer dropped."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_inv(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_inv_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            ["Misbehaving", f"inv message size = {MAX_INV_SZ + 1}"],
        ),
    ):
        peer.handshake()
        peer.send(_oversized_inv(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_getdata_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a `getdata` over `MAX_INV_SZ` gets the peer dropped."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_getdata(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_getdata_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            ["Misbehaving", f"getdata message size = {MAX_INV_SZ + 1}"],
        ),
    ):
        peer.handshake()
        peer.send(_oversized_getdata(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_headers_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: `headers` over `MAX_HEADERS_RESULTS` disconnects."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_headers(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_headers_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            ["Misbehaving", f"headers message size = {MAX_HEADERS_RESULTS + 1}"],
        ),
    ):
        peer.handshake()
        peer.send(_oversized_headers(), check_validity=False)
        peer.wait_for_disconnect()


def test_invalid_pow_header_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a header failing its own target disconnects."""
    header = _invalid_pow_header()
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Headers([header]))
        peer.wait_for_disconnect()


def test_invalid_pow_header_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    header = _invalid_pow_header()
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path,
            ["Misbehaving", "header with invalid proof of work"],
        ),
    ):
        peer.handshake()
        peer.send(Headers([header]))
        peer.wait_for_disconnect()
