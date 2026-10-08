# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak_tx`, one body per subject over either node.

Read from Core's `test/functional/p2p_leak_tx.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the clock and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`Capability.CLOCK` (`setmocktime`) is what holds the node's own
transaction-announcement clock still until this module is ready to
advance it, and `MiniWallet.send_self_transfer` (`Capability.MINE`) is
what funds each transaction without a node wallet. Each of Core's own
subjects becomes its own body, `Peer` and `NodeAdapter` standing
in for `P2PInterface`/`P2PDataStore`/`P2PTxInvStore` and a `TestNode`
(rule 5 of issue btclib-org/btclib#2220: tf2's own adapter and peer, not
btclib's `tests/integration/` fixture).

`tx_in_block` checks
`getrawmempool`'s own `mempool_sequence` and, where the build's own
`help getpeerinfo` names them (bitcoin/bitcoin#33448, which `v31.0rc1` is
the first tag to carry), `getpeerinfo`'s own
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

Each body starts a node of its own from the cluster it is handed rather
than sharing a session-scoped adapter: `mempool_sequence` is a counter
over the node's whole lifetime rather than per connection, so a shared
node would make each test's own exact reading depend on which other test
already ran against it, and `pytest-randomly` (`pyproject.toml`) does not
hold that order still.

`p2p_leak_tx_bitcoind_test.py` and `p2p_leak_tx_btclib_node_test.py` run
every body, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import GetData, Inv, Inventory, InventoryType, NotFound, TxPayload
from btclib.tx import Tx, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "notfound_on_replaced_tx",
    "notfound_on_unannounced_tx",
    "tx_in_block",
]

_MAGIC = magic_from_chain("regtest")

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's own advance, in every test below: long
# enough to cross `INVENTORY_BROADCAST_INTERVAL`, short enough that a
# single jump does it
_ANNOUNCE_ADVANCE = 120

# `Peer`'s own default wait, for a read that bypasses `wait_for`
_RECEIVE_TIMEOUT = 30.0


def _node(
    cluster: _Cluster, skip_counts: SkipCounts
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Start one node, asking it for `Capability.CLOCK` and then `MINE`."""
    (node,) = cluster(1)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    return node


def _reports_inv_fields(node: BitcoindAdapter | BtclibNodeAdapter) -> bool:
    """Return whether `node`'s own `help getpeerinfo` names the `inv` fields."""
    help_text = node.rpc.call("help", ["getpeerinfo"])
    assert isinstance(help_text, str)
    return "last_inv_sequence" in help_text and "inv_to_send" in help_text


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


def tx_in_block(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check that a tx just mined into the tip's own block is still uploaded.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    adapter = _node(cluster, skip_counts)
    reports_inv_fields = _reports_inv_fields(adapter)
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
        if reports_inv_fields:
            peer_info = adapter.rpc.call("getpeerinfo")[0]
            assert peer_info["last_inv_sequence"] == 1  # that is after the last inv
            assert peer_info["inv_to_send"] == 1  # and our tx has been queued

        mocktime += _ANNOUNCE_ADVANCE
        adapter.set_mock_time(mocktime)
        inv = _wait_for_inv(peer, tx.hash)

        rawmp = adapter.rpc.call("getrawmempool", [False, True])
        assert rawmp["mempool_sequence"] == 2  # no mempool update
        if reports_inv_fields:
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


def notfound_on_replaced_tx(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check that a getdata for a tx its replacement displaced answers notfound.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    adapter = _node(cluster, skip_counts)
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


def notfound_on_unannounced_tx(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check that a getdata for a tx not yet announced answers notfound.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    adapter = _node(cluster, skip_counts)
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
