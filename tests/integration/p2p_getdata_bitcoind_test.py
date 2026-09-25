# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getdata`, rewritten on this repository's own harness: bitcoind.

Read from Core's `test/functional/p2p_getdata.py` (`aaf9412026`,
2026-07-31) rather than ported: that file drives a `P2PInterface` over
Core's own asyncio harness and asserts against a `TestNode`'s own RPC.
Its subject is `test_invalid_getdata`: an invalid `getdata`
(`CInv(t=0, h=0)`) does not stop the node from answering a later valid
one, checked by a `ping`/`pong` round trip in between rather than a
timing guess. This rewrites that subject over `Peer` and `NodeAdapter`
(rule 5 of issue btclib-org/btclib#2220: tf2's own adapter, not
btclib's `tests/integration/` fixture).

One deviation, declared rather than silent: Core's own
`test_framework.py` seeds every node with 199 pre-mined blocks and
mines a 200th before a test runs, so the "later valid one" Core asks
for is that mined tip. `Capability.MINE` is not a fact this adapter can
supply to every node yet -- mining is step 4's, not this one's -- so
this asks for genesis instead, the one block every node this suite
drives already has without mining. That is a smaller claim than
Core's own, not the same one.

bitcoind is the oracle (rule 3), so this is the half that has to pass,
and it stands in a module of its own rather than beside btclib-node's:
`.github/workflows/node-integration.yml`'s bitcoind job runs this
directory through `btclib-org/.github`'s
`reusable-integration-bitcoind.yml`, whose own "did the node tests run"
check reads a testcase's classname, and a module is what that name is
built from -- the split is what lets that job's `exclude-classname` name
btclib-node's module and leave this one held to running, never skipping.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets

import pytest
from btclib.block import genesis_block
from btclib.p2p import BlockPayload, GetData, Inventory, Ping, Pong
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.peer import Peer

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_MSG_BLOCK = 2
_GENESIS_HASH = genesis_block("regtest").header.hash


def test_invalid_getdata_does_not_stop_a_later_valid_one(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """Core's own subject: the invalid item first, valid one still works."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()

        # CInv(t=0, h=0), Core's own invalid entry: InventoryType.UNDEFINED
        # is btclib's name for type 0, and Inventory()'s own defaults are
        # that type and a zero hash, so no argument names either explicitly
        peer.send(GetData([Inventory()]))

        # send_and_ping's own check: the node is still answering after the
        # invalid item, not merely still connected
        nonce = secrets.randbelow(2**63)
        peer.send(Ping(nonce))
        peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)

        peer.send(GetData([Inventory(_MSG_BLOCK, _GENESIS_HASH)]))
        message = peer.wait_for("block")
        received = BlockPayload.parse(message.payload, check_validity=False)
        assert received.block.header.hash == _GENESIS_HASH
