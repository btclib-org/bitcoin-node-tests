# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_feefilter`, as bodies over either node.

Read from Core's `test/functional/p2p_feefilter.py` (`fa5f29774872`,
2025-12-16): BIP133's `feefilter`, which a node sends a peer to say the
lowest fee rate it wants announced, and honours when a peer sends one.

Each of Core's own checks is a body over fresh nodes:

- a `feefilter` reaches an inbound peer, and none reaches one the
  `forcerelay` permission covers (`-whitelist=forcerelay@127.0.0.1`);
- a peer's own `feefilter` keeps the node from announcing a transaction
  paying less, and a `feefilter` of zero lifts it;
- no `feefilter` reaches a block-relay-only outbound peer
  (`Capability.TYPED_OUTBOUND`), nor any peer of a node under
  `-blocksonly` (`Capability.BLOCKS_ONLY`).

A check that no `feefilter` arrives reads the peer's own tally once
`Peer.sync_with_ping` returns, as Core's `assert_feefilter_received`
reads its flag once `add_p2p_connection`'s own ping returns: bitcoind
runs its send loop for the peer between the two pings, which is where it
sends one. The check that one arrives waits for it instead, since a node
answering the second ping ahead of the first
([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410))
sends it after the `pong`. On such a node a check that none arrives
cannot see one sent after the `pong`, so it passes whether or not the
node withholds it; bitcoind is the node whose barrier those checks rest
on. A fresh node is in initial block download, where Core's cached one
is not, so the filter it sends is Core's `MAX_MONEY` rounded down by
`FeeFilterRounder` to its largest bucket at or below
`MAX_FILTER_FEERATE`, rather than the minimum relay fee; only its
arrival is asserted, as in Core. The `-whitelist` asks for no
capability, as `rpc_setban.py`'s own `noban` row does not.

The filtering check funds its transactions from a `MiniWallet` on a
second node, relayed to the node under test over `connect_nodes`, as
Core's does; it asks for `Capability.MINE` of both nodes and
`Capability.CONNECT` of the second. The blocks reach the node under test
over `submitblock` before the two connect, so that neither is in initial
block download when they do: a node in it sends a filter far above any
rate paid here, and the funding node would then announce none of them to
it until the node under test sends its filter again. Every transaction
spends a matured coinbase of its own, as the coins of Core's cached
chain allow, so none is another's child. The withheld transactions are
checked the way Core checks them, by one of the node's own announced
after them, which holds where the node announces in one pass everything
queued for the peer. The last batch, once the filter is lifted, pays the
rate the filter withheld, where Core's pays 20 sat/vB, a rate the filter
lets through anyway. Core's own options are left out:
`-minrelaytxfee=0.00000100` restates its default at this row's pin
(`DEFAULT_MIN_RELAY_TX_FEE`, `src/policy/policy.h`), `-mintxfee` is a
floor of the node's own wallet, which no step funds a transaction
through, and the `noban` permission Core's harness gives every loopback
peer (`noban_tx_relay`) only makes a node announce at once rather than
on its own schedule. Each announcement is awaited for Core's own 60
seconds instead.

`p2p_feefilter_bitcoind_test.py` and `p2p_feefilter_btclib_node_test.py`
run each body, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import FeeFilter, Inv, InventoryType
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import (
    connect_nodes,
    wait_until_mempools_agree,
    wait_until_tips_agree,
)
from bitcoin_node_tests.peer import Listener, Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message
    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "feefilter_filters_announcements",
    "feefilter_is_not_sent_in_blocks_only_mode",
    "feefilter_is_not_sent_to_a_block_relay_only_peer",
    "feefilter_is_not_sent_to_a_forcerelay_peer",
    "feefilter_is_sent_to_an_inbound_peer",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's own fee rates, in satoshis per 1000 virtual bytes
_RECEIVED_RATE = 200
_FILTER_RATE = 150
_FILTERED_RATE = 100
_HIGH_RATE = 20000

# how many transactions each of Core's steps sends from the second node
_BATCH = 3

# every batch, and the one transaction sent from the node under test
_SPENDS = 4 * _BATCH + 1

# Core's own wait, `P2PInterface.wait_until`'s and `sync_mempools`'s default
_WAIT = 60.0


def _connect(node: NodeAdapter) -> Peer:
    """Core's own `add_p2p_connection`: a handshake, then a ping round trip."""
    peer = Peer(node.p2p_address, magic_from_chain(node.chain))
    try:
        peer.handshake()
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer


def _send_and_ping(peer: Peer, feerate: int) -> None:
    """Core's own `send_and_ping(msg_feefilter(feerate))`."""
    peer.send(FeeFilter(feerate))
    peer.sync_with_ping()


def _wait_for_tx_invs(peer: Peer, expected: set[bytes]) -> None:
    """Core's own `wait_for_invs_to_match`, from what `peer` reads from now.

    Every `inv` read is gathered, its transaction entries' hashes kept,
    until they hold every one of `expected`; an announcement beyond them
    read by then fails the equality, as it fails Core's own.

    :param expected: the wtxids to wait for.
    :raises TimeoutError: `expected` was not all announced in time.
    """
    announced: set[bytes] = set()

    def _complete(message: Message) -> bool:
        announced.update(
            item.hash
            for item in Inv.parse(message.payload).items
            if item.type_code in {InventoryType.MSG_TX, InventoryType.MSG_WTX}
        )
        return expected <= announced

    peer.wait_for("inv", predicate=_complete, timeout=_WAIT)
    assert announced == expected


def _send_batch(wallet: MiniWallet, fee_rate: int) -> set[bytes]:
    """Send `_BATCH` self-transfers over `wallet`'s node; return the wtxids."""
    return {wallet.send_self_transfer(fee_rate=fee_rate).hash for _ in range(_BATCH)}


def _send_from(node: NodeAdapter, tx: Tx) -> None:
    """Broadcast `tx` over `node`: Core's own `from_node`, `maxfeerate` 0."""
    tx_hex = tx.serialize(True, check_validity=False).hex()
    assert node.rpc.call("sendrawtransaction", [tx_hex, 0]) == tx.id.hex()


def feefilter_is_sent_to_an_inbound_peer(cluster: _Cluster) -> None:
    """Check a peer the node grants no permission gets a `feefilter`.

    Asks for no capability.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    """
    (node,) = cluster(1)
    with _connect(node) as peer:
        if peer.message_count["feefilter"] == 0:
            peer.wait_for("feefilter")


def feefilter_is_not_sent_to_a_forcerelay_peer(cluster: _Cluster) -> None:
    """Check a peer holding the `forcerelay` permission gets no `feefilter`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    """
    (node,) = cluster(1)
    node.restart(["-whitelist=forcerelay@127.0.0.1"])
    with _connect(node) as peer:
        assert peer.message_count["feefilter"] == 0


def feefilter_filters_announcements(cluster: _Cluster, skip_counts: SkipCounts) -> None:
    """Check a peer's own `feefilter` withholds what pays less, and lifts.

    Core's own `test_feefilter`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, funder = cluster(2)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.MINE, funder.capabilities, skip_counts)
    require(Capability.CONNECT, funder.capabilities, skip_counts)
    wallet = MiniWallet(funder)
    for block_hash in wallet.generate(COINBASE_MATURITY + _SPENDS - 1):
        block_hex = funder.rpc.call("getblock", [block_hash.hex(), 0])
        assert node.rpc.call("submitblock", [block_hex]) is None
    wait_until_tips_agree([node, funder])
    connect_nodes(funder, node)

    with _connect(node) as conn:
        # paying 0.2 sat/vB, announced
        _wait_for_tx_invs(conn, _send_batch(wallet, _RECEIVED_RATE))

        _send_and_ping(conn, _FILTER_RATE)

        # paying 0.15 sat/vB, announced
        _wait_for_tx_invs(conn, _send_batch(wallet, _FILTER_RATE))

        # paying 0.1 sat/vB, withheld: once the node holds them, one of its
        # own is announced, and none of these may be announced beside it
        _send_batch(wallet, _FILTERED_RATE)
        wait_until_mempools_agree([node, funder], timeout=_WAIT)
        tx = wallet.create_self_transfer(fee_rate=_HIGH_RATE)
        _send_from(node, tx)
        _wait_for_tx_invs(conn, {tx.hash})
        wait_until_mempools_agree([node, funder], timeout=_WAIT)

        # a `feefilter` of zero, and they are announced again
        _send_and_ping(conn, 0)
        _wait_for_tx_invs(conn, _send_batch(wallet, _FILTERED_RATE))


def feefilter_is_not_sent_to_a_block_relay_only_peer(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a block-relay-only outbound peer gets no `feefilter`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    with Listener(magic_from_chain(node.chain)) as listener:
        node.add_outbound_connection(listener.address, "block-relay-only")
        peer = listener.accept()
    with peer:
        peer.handshake()
        peer.sync_with_ping()
        assert peer.message_count["feefilter"] == 0


def feefilter_is_not_sent_in_blocks_only_mode(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a node under `-blocksonly` sends an inbound peer no `feefilter`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.BLOCKS_ONLY, node.capabilities, skip_counts)
    node.restart(["-blocksonly"])
    with _connect(node) as peer:
        assert peer.message_count["feefilter"] == 0
