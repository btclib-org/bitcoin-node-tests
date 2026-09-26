# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same four checks: btclib-node.

`p2p_invalid_messages_misbehaving_bitcoind_test.py`'s own docstring is
where the four Core checks this splits into a wire half and a log half
are argued. The wire half is the same fact on this node too, reached
differently: `btclib_node.p2p.main.handle_p2p` stops a connection whose
own callback raised a `BTClibException`
(`btclib_node.p2p.main`, "A `BTClibException` is btclib refusing this
peer's own wire content"), and `Inv.parse`, `GetData.parse` and
`Headers.parse` (`btclib.p2p.inventory`) each refuse a count over its own
bound before this node's own callback reads a single entry --
`callbacks.py`'s own `handle_inv`, `handle_getdata` and `handle_headers`
call them directly on the message this test sends. The invalid-PoW
header is the same shape one layer further in:
`chainstate.block_index.BlockIndex.add_headers` calls
`BlockHeader.assert_valid_pow`, whose refusal is the same
`BTClibException` this node's own dispatcher already stops the
connection for.

The log half is not: this node's own `Logger` (`log.py`) writes English,
not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and all four log checks skip.

`test_oversized_inv_disconnects_the_peer` is expected to fail rather
than to pass or to skip -- neither an `xfail` nor a
`pytest.skip.Exception` -- so this keeps reproducing
[ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)
rather than hiding it: `p2p.callbacks.inv` returns before calling
`Inv.parse` at all while `node.status < NodeStatus.BlockSynced`, a
status this adapter's own lone, peerless node never advances past, so
an oversized `inv` is dropped unread rather than refused. The other
three wire checks reach `GetData.parse`, `Headers.parse` and
`assert_valid_pow` with no such guard in front of them, and pass.
`TF2.md`'s per-test table carries the verdict this failure is, not a
decoration on this module.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
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
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
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

    The same search as the bitcoind module's own, over the same genesis
    parent: each call stamps its own time, so the octets differ from call
    to call, and every header it returns is one Core's own
    `CheckHeadersPoW` refuses.
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


def test_oversized_inv_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_inv(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_inv_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_oversized_getdata_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_getdata(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_getdata_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_oversized_headers_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_headers(), check_validity=False)
        peer.wait_for_disconnect()


def test_oversized_headers_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_invalid_pow_header_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: a header built as the bitcoind module builds its own."""
    header = _invalid_pow_header()
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Headers([header]))
        peer.wait_for_disconnect()


def test_invalid_pow_header_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
