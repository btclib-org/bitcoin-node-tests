# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak_tx`, rewritten on this repository's own harness: bitcoind.

Read from Core's `test/functional/p2p_leak_tx.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the clock and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`Capability.CLOCK` (`setmocktime`) is what holds the node's own
transaction-announcement clock still until this module is ready to
advance it, and `MiniWallet.send_self_transfer` (`Capability.MINE`) is
what funds each transaction without a node wallet. Each of Core's own
subjects becomes its own test, `Peer` and `NodeAdapter` standing
in for `P2PInterface`/`P2PDataStore`/`P2PTxInvStore` and a `TestNode`
(rule 5 of issue btclib-org/btclib#2220: tf2's own adapter and peer, not
btclib's `tests/integration/` fixture).

`test_tx_in_block` checks
`getrawmempool`'s own `mempool_sequence` and `getpeerinfo`'s own
`last_inv_sequence`/`inv_to_send` around a broadcast and the `inv` it
produces once the mock clock advances, builds a `getdata` from that
`inv`, mines the transaction into a block, and only then sends the
`getdata`: a transaction that has just left the mempool for the most
recent block is still uploaded, which Core's own log line calls
beneficial for compact block relay.

Every connection is synced with a ping after its handshake, as Core's
`TestNode.add_p2p_connection` does: `Peer.handshake` returns before the
node has processed this peer's own `verack`, and Core's comment there
names the race that leaves, a transaction added to the mempool as soon
as the handshake returns.

Each test starts its own node rather than sharing the session-scoped
`bitcoind_adapter` fixture: `mempool_sequence` is a counter over the
node's whole lifetime rather than per connection, so a shared node would
make each test's own exact reading depend on which other test already
ran against it, and `pytest-randomly` (`pyproject.toml`) does not hold
that order still.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import GetData, Inv, Inventory, InventoryType, NotFound, TxPayload
from btclib.p2p.magic import magic_from_chain
from btclib.tx import Tx, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")


def _start_adapter(bitcoind_path: str, tmp_path: Path) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(bitcoind_path, tmp_path, rpc_port, p2p_port)
    adapter.start()
    return adapter


# Core's own advance, in every test below: long
# enough to cross `INVENTORY_BROADCAST_INTERVAL`, short enough that a
# single jump does it
_ANNOUNCE_ADVANCE = 120

# `Peer`'s own default wait, for a read that bypasses `wait_for`
_RECEIVE_TIMEOUT = 30.0


def _wait_for_inv(peer: Peer, tx_hash: bytes) -> Inv:
    """Wait for an `inv` naming `tx_hash` as an `MSG_WTX`, and return it."""
    message = peer.wait_for(
        "inv",
        predicate=lambda m: any(
            item.type_code == InventoryType.MSG_WTX and item.hash == tx_hash
            for item in Inv.parse(m.payload).items
        ),
    )
    return Inv.parse(message.payload)


def test_tx_in_block(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A tx just mined into the tip's own block is still uploaded."""
    require(Capability.CLOCK, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        mocktime = int(time.time())
        adapter.set_mock_time(mocktime)

        with Peer(adapter.p2p_address, _MAGIC) as peer:
            peer.handshake()
            peer.sync_with_ping()

            tx = wallet.send_self_transfer()
            rawmp = adapter.rpc.call("getrawmempool", [False, True])
            assert rawmp["mempool_sequence"] == 2  # our tx caused mempool activity
            peer_info = adapter.rpc.call("getpeerinfo")[0]
            assert peer_info["last_inv_sequence"] == 1  # that is after the last inv
            assert peer_info["inv_to_send"] == 1  # and our tx has been queued

            mocktime += _ANNOUNCE_ADVANCE
            adapter.set_mock_time(mocktime)
            inv = _wait_for_inv(peer, tx.hash)

            rawmp = adapter.rpc.call("getrawmempool", [False, True])
            assert rawmp["mempool_sequence"] == 2  # no mempool update
            peer_info = adapter.rpc.call("getpeerinfo")[0]
            assert peer_info["last_inv_sequence"] == 2  # announced the current mempool
            assert peer_info["inv_to_send"] == 0  # nothing left in the queue

            want_tx = GetData(inv.items)
            wallet.generate(1, confirm=[tx])
            assert adapter.rpc.call("getrawmempool") == []  # the tx left for the block

            peer.send(want_tx)
            message = peer.wait_for("tx")
            parsed = TxPayload.parse(message.payload, check_validity=False)
            assert parsed.tx.hash == tx.hash
    finally:
        adapter.stop()


def test_notfound_on_replaced_tx(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A getdata for a tx its own replacement displaced answers notfound."""
    require(Capability.CLOCK, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        mocktime = int(time.time())
        adapter.set_mock_time(mocktime)

        with Peer(adapter.p2p_address, _MAGIC) as peer:
            peer.handshake()
            peer.sync_with_ping()

            tx_a = wallet.send_self_transfer()
            mocktime += _ANNOUNCE_ADVANCE
            adapter.set_mock_time(mocktime)
            _wait_for_inv(peer, tx_a.hash)

            replaced_out = TxOut(tx_a.vout[0].value - 9000, tx_a.vout[0].script_pub_key)
            tx_b = Tx(
                version=tx_a.version,
                lock_time=tx_a.lock_time,
                vin=list(tx_a.vin),
                vout=[replaced_out],
            )
            adapter.rpc.call(
                "sendrawtransaction",
                [tx_b.serialize(True, check_validity=False).hex()],
            )
            mocktime += _ANNOUNCE_ADVANCE
            adapter.set_mock_time(mocktime)
            _wait_for_inv(peer, tx_b.hash)

            peer.send(
                GetData(
                    [
                        Inventory(InventoryType.MSG_TX, tx_a.id),
                        Inventory(InventoryType.MSG_WTX, tx_a.hash),
                    ]
                )
            )
            # the node sends whatever it finds ahead of its own `notfound`,
            # so a `tx` for either request would arrive first
            message = peer.receive(timeout=scaled(_RECEIVE_TIMEOUT))
            while message.command != "notfound":
                assert message.command != "tx"
                message = peer.receive(timeout=scaled(_RECEIVE_TIMEOUT))
            received = NotFound.parse(message.payload)
            assert [(item.type_code, item.hash) for item in received.items] == [
                (InventoryType.MSG_TX, tx_a.id),
                (InventoryType.MSG_WTX, tx_a.hash),
            ]
    finally:
        adapter.stop()


def test_notfound_on_unannounced_tx(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A getdata for a tx not yet announced to this peer answers notfound."""
    require(Capability.CLOCK, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        mocktime = int(time.time())
        adapter.set_mock_time(mocktime)

        with Peer(adapter.p2p_address, _MAGIC) as peer:
            peer.handshake()
            peer.sync_with_ping()

            # the mock clock does not move, so the node never announces this
            # transaction on its own
            tx = wallet.send_self_transfer()

            peer.send(GetData([Inventory(InventoryType.MSG_WTX, tx.hash)]))
            message = peer.wait_for("notfound")
            received = NotFound.parse(message.payload)
            assert received.items[0].hash == tx.hash

            mocktime += _ANNOUNCE_ADVANCE
            adapter.set_mock_time(mocktime)
            _wait_for_inv(peer, tx.hash)

            peer.send(GetData([Inventory(InventoryType.MSG_WTX, tx.hash)]))
            message = peer.wait_for("tx")
            parsed = TxPayload.parse(message.payload, check_validity=False)
            assert parsed.tx.id == tx.id
    finally:
        adapter.stop()
