# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_orphans`, one body per subtest over either node.

Read from Core's `test/functional/rpc_orphans.py` (`fa5f29774872`,
2025-12-16): a peer sends a child ahead of its own parent, the node keeps
it as an orphan and reports it over `getorphantxs`
(`Capability.ORPHANAGE`), and the parent arriving later brings the child
into the mempool. Each of Core's own subtests is a function here, run on
a node of its own, and every assertion Core's file makes is kept.

`MiniWallet` (`Capability.MINE`) builds every parent and child, as in
Core. It needs mature coins, so it first mines past `COINBASE_MATURITY`,
where Core's own node starts on a chain its framework already mined, and
the block Core's `test_orphan_activity` ends on is one it mines carrying
the transactions that subtest sent.

`Peer` stands in for Core's `P2PInterface`, connected and synced with a
ping as `TestNode.add_p2p_connection` does, and `send_and_ping` is a
`send` followed by `Peer.sync_with_ping`. `in_orphanage` is Core's own
`tx_in_orphanage` (`test_framework/mempool_util.py`).

`rpc_orphans_bitcoind_test.py` and `rpc_orphans_btclib_node_test.py` run
each body, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError, magic_from_chain
from btclib.p2p import Inv, Inventory, InventoryType, TxPayload
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Payload
    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "getorphantxs_is_hidden_and_refuses_a_boolean_verbosity",
    "getorphantxs_reports_each_orphan_and_its_announcers",
    "in_orphanage",
    "orphans_leave_the_orphanage_with_their_parents",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# `src/rpc/protocol.h`'s own codes for the refusals asserted below
_INVALID_PARAMETER = -8
_TYPE_ERROR = -3

# the parents each subtest spends a coin on, mature by the time it does
_COINS = 2


def _node(
    cluster: _Cluster, skip_counts: SkipCounts, *, mine: bool = True
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Start one node, asking it for `Capability.ORPHANAGE` and then `MINE`.

    :param mine: where false, `MINE` is not asked for, the subtest
        building no transaction.
    """
    (node,) = cluster(1)
    require(Capability.ORPHANAGE, node.capabilities, skip_counts)
    if mine:
        require(Capability.MINE, node.capabilities, skip_counts)
    return node


def _peer(node: NodeAdapter, stack: ExitStack) -> Peer:
    """Core's `add_p2p_connection`: a handshake, then a ping to sync on."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _send_and_ping(peer: Peer, payload: Payload) -> None:
    """Core's `send_and_ping`: `payload`, then a ping answered after it."""
    peer.send(payload)
    peer.sync_with_ping()


def _parent_and_child(wallet: MiniWallet) -> tuple[Tx, Tx]:
    """Return an unbroadcast self-transfer and another spending its output."""
    parent = wallet.create_self_transfer()
    coin = wallet.new_utxos(parent)[0]
    return parent, wallet.create_self_transfer(utxo_to_spend=coin)


def _orphans(node: NodeAdapter, verbosity: int) -> list[dict[str, object]]:
    """Return `getorphantxs` at `verbosity`, each orphan an object."""
    orphanage = node.rpc.call("getorphantxs", {"verbosity": verbosity})
    assert isinstance(orphanage, list)
    return orphanage


def in_orphanage(node: NodeAdapter, tx: Tx) -> bool:
    """Core's `tx_in_orphanage`: `tx` is kept, by txid and wtxid, once."""
    found = [
        orphan
        for orphan in _orphans(node, 1)
        if orphan["txid"] == tx.id.hex() and orphan["wtxid"] == tx.hash.hex()
    ]
    return len(found) == 1


def _refused(
    node: NodeAdapter, params: dict[str, object], code: int, message: str
) -> None:
    """Core's `assert_raises_rpc_error` for `getorphantxs`, by substring.

    Of the node's own message alone: `RpcError`'s text opens with the
    method and the endpoint (`bitcoin_core_rpc`'s own `_result`), so a
    `message` naming the method would match that prefix whatever the node
    answered.
    """
    client = node.rpc
    with pytest.raises(RpcError) as excinfo:
        client.call("getorphantxs", params)
    assert excinfo.value.code == code
    where = f"getorphantxs at {client.url}: "
    assert excinfo.value.args[0].startswith(where)
    assert message in excinfo.value.args[0].removeprefix(where)


def _details_match(orphan: dict[str, object], tx: Tx, *, verbosity: int) -> None:
    """Core's `orphan_details_match`: the ids, the sizes and, at 2, the hex."""
    serialized = tx.serialize(True, check_validity=False)
    assert orphan["txid"] == tx.id.hex()
    assert orphan["wtxid"] == tx.hash.hex()
    assert orphan["bytes"] == len(serialized)
    assert orphan["vsize"] == tx.vsize
    assert orphan["weight"] == tx.weight
    if verbosity == 2:
        assert orphan["hex"] == serialized.hex()


def orphans_leave_the_orphanage_with_their_parents(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_orphan_activity`: two orphans kept, and each let go.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _node(cluster, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + _COINS)

    # two one-parent-one-child packages, only the children broadcast
    parent_1, child_1 = _parent_and_child(wallet)
    parent_2, child_2 = _parent_and_child(wallet)
    with ExitStack() as stack:
        peer = _peer(node, stack)
        _send_and_ping(peer, TxPayload(child_1, True))
        _send_and_ping(peer, TxPayload(child_2, True))

        # neither parent is in the mempool, and both children are orphans
        assert node.rpc.call("getmempoolinfo")["size"] == 0
        assert len(_orphans(node, 0)) == 2
        _refused(
            node, {"verbosity": -1}, _INVALID_PARAMETER, "Invalid verbosity value -1"
        )
        _refused(
            node, {"verbosity": 3}, _INVALID_PARAMETER, "Invalid verbosity value 3"
        )
        assert in_orphanage(node, child_1)
        assert in_orphanage(node, child_2)

        # parent 1 brings child 1 into the mempool, leaving child 2 an orphan
        _send_and_ping(peer, TxPayload(parent_1, True))
        raw_mempool = node.rpc.call("getrawmempool")
        assert len(raw_mempool) == 2
        assert parent_1.id.hex() in raw_mempool
        assert child_1.id.hex() in raw_mempool
        assert len(node.rpc.call("getorphantxs")) == 1
        assert in_orphanage(node, child_2)

        # parent 2 brings child 2 in, leaving the orphanage empty
        _send_and_ping(peer, TxPayload(parent_2, True))
        raw_mempool = node.rpc.call("getrawmempool")
        assert len(raw_mempool) == 4
        for tx in (parent_1, child_1, parent_2, child_2):
            assert tx.id.hex() in raw_mempool
        assert len(node.rpc.call("getorphantxs")) == 0

        # a block confirming all four clears the mempool
        wallet.generate(1, confirm=[parent_1, child_1, parent_2, child_2])
        assert node.rpc.call("getmempoolinfo")["size"] == 0


def getorphantxs_reports_each_orphan_and_its_announcers(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_orphan_details`: who sent each orphan, and what it is.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _node(cluster, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + _COINS)

    # two orphans, each from a peer of its own
    _, child_1 = _parent_and_child(wallet)
    parent_2, child_2 = _parent_and_child(wallet)
    with ExitStack() as stack:
        peer_1 = _peer(node, stack)
        peer_2 = _peer(node, stack)
        _send_and_ping(peer_1, TxPayload(child_1, True))
        _send_and_ping(peer_2, TxPayload(child_2, True))

        orphanage = _orphans(node, 2)
        assert in_orphanage(node, child_1)
        assert in_orphanage(node, child_2)
        first_from, second_from = orphanage[0]["from"], orphanage[1]["from"]
        assert isinstance(first_from, list)
        assert isinstance(second_from, list)
        assert first_from[0] != second_from[0]
        peer_ids = {first_from[0], second_from[0]}

        # child 2 leaves with its parent
        _send_and_ping(peer_2, TxPayload(parent_2, True))
        assert not in_orphanage(node, child_2)

        # a second announcer of child 1 is reported beside the first
        _send_and_ping(peer_2, Inv([Inventory(InventoryType.MSG_WTX, child_1.hash)]))
        orphanage = _orphans(node, 2)
        announcers = orphanage[0]["from"]
        assert isinstance(announcers, list)
        assert set(announcers) == peer_ids

        assert len(node.rpc.call("getorphantxs")) == 1
        _details_match(orphanage[0], child_1, verbosity=1)
        _details_match(_orphans(node, 2)[0], child_1, verbosity=2)


def getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_misc`: a boolean verbosity refused, and `help` silent on it.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _node(cluster, skip_counts, mine=False)
    message = "Verbosity was boolean but only integer allowed"
    _refused(node, {"verbosity": True}, _TYPE_ERROR, message)
    _refused(node, {"verbosity": False}, _TYPE_ERROR, message)
    assert "getorphantxs" not in node.rpc.call("help")
    assert "unknown command: getorphantxs" not in node.rpc.call(
        "help", ["getorphantxs"]
    )
