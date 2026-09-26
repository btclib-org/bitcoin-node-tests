# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_locator`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_invalid_locator.py` (`fa5f29774872`,
2025-12-16): a locator over `MAX_LOCATOR_SZ` gets the sending peer
disconnected, for both `getheaders` and `getblocks`; one at the bound
gets an ordinary answer instead -- a `headers` message for the first, an
`inv` for the second. Core's own node starts from a 200-block cached
chain; this one mines its own, past `MAX_LOCATOR_SZ` so that every
height a locator names exists (`Capability.MINE`, over bitcoind's own
wallet).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.p2p import GetBlocks, GetHeaders, Headers, Inv, InventoryType
from btclib.p2p.limits import MAX_LOCATOR_SZ
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")


def _locator(adapter: BitcoindAdapter, block_count: int, length: int) -> list[bytes]:
    """Return `length` block hashes, from `block_count` backwards."""
    hashes = []
    for height in range(block_count, block_count - length, -1):
        block_hash = adapter.rpc.call("getblockhash", [height - 1])
        hashes.append(bytes.fromhex(str(block_hash)))
    return hashes


def _assert_disconnects_on(
    adapter: BitcoindAdapter, locator: list[bytes], *, getheaders: bool
) -> None:
    """Send `locator`, and wait for the connection itself to close.

    `handshake` only drains what it sees ahead of the node's own
    `verack`; `sendaddrv2`, `sendcmpct`, `feefilter` and the node's own
    `getheaders` can each land after it, still unread once `handshake`
    returns -- Core's own `wait_for_disconnect` keeps pumping every
    message regardless, over a background thread, which is what a
    single `receive` call does not do on its own, so this loops it.
    """
    message = (
        GetHeaders(locator=locator, check_validity=False)
        if getheaders
        else GetBlocks(locator=locator, check_validity=False)
    )
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(message, check_validity=False)
        with pytest.raises(ConnectionError):
            while True:
                peer.receive(timeout=scaled(10.0))


def _assert_answers_within(
    adapter: BitcoindAdapter,
    locator: list[bytes],
    best_hash: bytes,
    *,
    getheaders: bool,
) -> None:
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        if getheaders:
            peer.send(GetHeaders(locator=locator))
            response = peer.wait_for("headers")
            headers = Headers.parse(response.payload)
            assert any(header.hash == best_hash for header in headers.headers)
        else:
            peer.send(GetBlocks(locator=locator))
            response = peer.wait_for("inv")
            inventory = Inv.parse(response.payload)
            assert any(
                item.type_code == InventoryType.MSG_BLOCK and item.hash == best_hash
                for item in inventory.items
            )


def test_max_locator_size(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject: over the bound disconnects, at the bound answers."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    bitcoind_adapter.mine(MAX_LOCATOR_SZ + 10)
    block_count = bitcoind_adapter.rpc.call("getblockcount")
    if not isinstance(block_count, int):
        err_msg = f"getblockcount answered {block_count!r}, not an int"
        raise TypeError(err_msg)
    best_hash_raw = bitcoind_adapter.rpc.call("getbestblockhash")
    best_hash = bytes.fromhex(str(best_hash_raw))

    for getheaders in (True, False):
        exceeding = _locator(bitcoind_adapter, block_count, MAX_LOCATOR_SZ + 1)
        _assert_disconnects_on(bitcoind_adapter, exceeding, getheaders=getheaders)

        within = _locator(bitcoind_adapter, block_count, MAX_LOCATOR_SZ)
        _assert_answers_within(
            bitcoind_adapter, within, best_hash, getheaders=getheaders
        )
