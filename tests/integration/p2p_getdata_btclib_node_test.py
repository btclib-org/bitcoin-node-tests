# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getdata`, rewritten on tf2's own harness: btclib-node.

The same request `p2p_getdata_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
an invalid `getdata` does not stop a later valid one from being served,
asked for genesis rather than Core's own mined tip -- that module's own
docstring has why. Held in its own module so that a job running one and
not the other -- `.github/workflows/node-integration.yml`'s bitcoind
job, which has no btclib-node interpreter to reach for -- can exclude
this module's own classname from its "did the node tests run" check by
name rather than by test name, a JUnit `classname` being a module's and
not a function's.

Expected to fail rather than to pass or to skip -- neither an `xfail`
nor a `pytest.skip.Exception` -- so this keeps reproducing
[ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)
rather than hiding it: `block_db` never stores genesis, so neither this
nor `getblock` can serve the one block a fresh regtest node, mined or
not, starts at. `TF2.md`'s per-test table carries the verdict this
failure is, not a decoration on this module.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_getdata_btclib_node_test.py
"""

from __future__ import annotations

import secrets

import pytest
from btclib.block import genesis_block
from btclib.p2p import BlockPayload, GetData, Inventory, Ping, Pong
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.peer import Peer

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_MSG_BLOCK = 2
_GENESIS_HASH = genesis_block("regtest").header.hash


def test_invalid_getdata_does_not_stop_a_later_valid_one(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the same request `p2p_getdata_bitcoind_test.py` makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()

        # CInv(t=0, h=0), Core's own invalid entry
        peer.send(GetData([Inventory()]))

        nonce = secrets.randbelow(2**63)
        peer.send(Ping(nonce))
        peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)

        peer.send(GetData([Inventory(_MSG_BLOCK, _GENESIS_HASH)]))
        message = peer.wait_for("block")
        received = BlockPayload.parse(message.payload, check_validity=False)
        assert received.block.header.hash == _GENESIS_HASH
