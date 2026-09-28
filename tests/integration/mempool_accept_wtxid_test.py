# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_accept_wtxid`, one body over either node.

Read from Core's `test/functional/mempool_accept_wtxid.py`
(`3f5211cba8e7`, 2026-01-21): two children of one parent share a txid
and differ only in the witness that spends it. The node admits the first,
refuses the second at `testmempoolaccept` as a transaction whose
non-witness data its mempool already holds, and answers the second's own
`sendrawtransaction` by announcing the first again, by its own wtxid, to a
peer that has not seen it. Every assertion Core's file makes is kept.

`MiniWallet` (`Capability.MINE`) funds the parent, as in Core. It needs a
mature coin, so it first mines one block past `COINBASE_MATURITY`, where
Core's own node starts on a chain its framework already mined, and the
block confirming the parent is one it mines carrying that parent. The
parent is broadcast over `sendrawtransaction` directly rather than
through the wallet, whose cache nothing below reads again.

`malleated_package` is Core's own `build_malleated_tx_package`
(`test_framework/script_util.py`), built with btclib's script and
transaction types: a parent paying a P2WSH output whose script has two
branches, and two children spending it, one through each.

`Peer` stands in for Core's `P2PTxInvStore`, connected and synced with a
ping as `TestNode.add_p2p_connection` does. `_wait_for_broadcast` is its
`wait_for_broadcast`, answering each `inv` with a `getdata` for what it
names, as `P2PInterface.on_inv` does: that request is what takes a
transaction out of the node's own unbroadcast set, which
`getmempoolinfo`'s `unbroadcastcount` then reads as empty.

`mempool_accept_wtxid_bitcoind_test.py` and
`mempool_accept_wtxid_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from contextlib import ExitStack, suppress
from typing import TYPE_CHECKING

from btclib.hashes import hash160
from btclib.p2p import GetData, Inv, InventoryType, Ping, Pong
from btclib.p2p.magic import magic_from_chain
from btclib.script.script import serialize as script_serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
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
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_child_sharing_a_txid_is_told_apart_by_its_wtxid",
    "malleated_package",
]

_MAGIC = magic_from_chain("regtest")

# Core's own `wait_for_broadcast` default, in seconds
_BROADCAST_TIMEOUT = 60.0

# satoshis Core's own file leaves in the parent's own output, moving the
# rest to the P2WSH one, and then leaves to each child as its fee
_REBALANCE_MARGIN = 10_000

# the preimage Core's own `build_malleated_tx_package` hashes for its lock
_PREIMAGE = b"Preimage"

_TX_TYPES = frozenset({InventoryType.MSG_TX, InventoryType.MSG_WTX})


def malleated_package(
    parent: Tx, rebalance_parent_output_amount: int, child_amount: int
) -> tuple[Tx, Tx, Tx]:
    """Core's `build_malleated_tx_package`: a parent and two malleated children.

    The parent's last output gives `rebalance_parent_output_amount` to a
    P2WSH output whose script is `OP_IF OP_HASH160 <hash160(preimage)>
    OP_EQUAL OP_ELSE OP_TRUE OP_ENDIF`; each child spends it into a P2WSH
    `OP_TRUE` output of `child_amount`, the first through the hashlock
    branch and the second through the other, so the two share their
    non-witness data and a txid.

    :param parent: an anyone-can-spend transaction, `MiniWallet`'s own;
        not mutated, the parent returned being a new one.
    :returns: the parent, and the two children spending its new output.
    """
    witness_script = script_serialize(
        [
            "OP_IF",
            "OP_HASH160",
            hash160(_PREIMAGE),
            "OP_EQUAL",
            "OP_ELSE",
            "OP_1",
            "OP_ENDIF",
        ]
    )
    last = parent.vout[-1]
    assert last.value >= rebalance_parent_output_amount
    new_parent = Tx(
        version=parent.version,
        lock_time=parent.lock_time,
        vin=list(parent.vin),
        vout=[
            *parent.vout[:-1],
            TxOut(last.value - rebalance_parent_output_amount, last.script_pub_key),
            TxOut(
                rebalance_parent_output_amount,
                ScriptPubKey.p2wsh(witness_script, "regtest"),
            ),
        ],
    )
    outpoint = OutPoint(new_parent.id, len(new_parent.vout) - 1)
    child_output = TxOut(
        child_amount, ScriptPubKey.p2wsh(script_serialize(["OP_1"]), "regtest")
    )

    def child(stack: list[bytes]) -> Tx:
        return Tx(
            version=2,
            lock_time=0,
            vin=[TxIn(outpoint, b"", 0, Witness(stack))],
            vout=[child_output],
        )

    return (
        new_parent,
        child([_PREIMAGE, b"\x01", witness_script]),
        child([b"", witness_script]),
    )


def _peer(node: NodeAdapter, stack: ExitStack) -> Peer:
    """Core's `add_p2p_connection`: a handshake, then a ping to sync on."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _wait_for_broadcast(peer: Peer, wtxids: set[bytes]) -> None:
    """Core's `P2PTxInvStore.wait_for_broadcast`, requesting what is announced.

    Returns once the transactions `peer` has seen announced are exactly
    `wtxids`, then syncs with a ping so that the node has served each
    `getdata` sent meanwhile.

    :raises TimeoutError: the announcements seen still differ from
        `wtxids` after `_BROADCAST_TIMEOUT`, scaled.
    """
    announced: set[bytes] = set()
    deadline = time.monotonic() + scaled(_BROADCAST_TIMEOUT)
    while announced != wtxids:
        remaining = deadline - time.monotonic()
        message = None
        if remaining > 0:
            with suppress(TimeoutError):
                message = peer.receive(timeout=remaining)
        if message is None:
            err_msg = f"announced {announced!r}, never exactly {wtxids!r}"
            raise TimeoutError(err_msg)
        if message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            wanted = [
                item for item in items if item.type_code != InventoryType.UNDEFINED
            ]
            if wanted:
                peer.send(GetData(wanted))
            announced |= {item.hash for item in items if item.type_code in _TX_TYPES}
    peer.sync_with_ping()


def _raw(tx: Tx) -> str:
    """Return `tx`'s own hex, witness included, for `sendrawtransaction`."""
    return tx.serialize(True, check_validity=False).hex()


def _refusal(tx: Tx, reason: str) -> dict[str, object]:
    """Return `testmempoolaccept`'s own entry refusing `tx` for `reason`."""
    return {
        "txid": tx.id.hex(),
        "wtxid": tx.hash.hex(),
        "allowed": False,
        "reject-reason": reason,
        "reject-details": reason,
    }


def a_child_sharing_a_txid_is_told_apart_by_its_wtxid(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    assert node.rpc.call("getmempoolinfo")["size"] == 0

    # a parent whose new output two scripts' branches can spend
    unmodified = wallet.create_self_transfer()
    parent_amount = unmodified.vout[0].value - _REBALANCE_MARGIN
    child_amount = parent_amount - _REBALANCE_MARGIN
    parent, child_one, child_two = malleated_package(
        unmodified, parent_amount, child_amount
    )
    assert node.rpc.call("sendrawtransaction", [_raw(parent), 0]) == parent.id.hex()
    wallet.generate(1, confirm=[parent])

    with ExitStack() as stack:
        peer_wtxid_relay = _peer(node, stack)

        assert child_one.id == child_two.id
        assert child_one.hash != child_two.hash

        # child one enters the mempool, and is announced by its own wtxid
        txid_submitted = node.rpc.call("sendrawtransaction", [_raw(child_one)])
        entry = node.rpc.call("getmempoolentry", [txid_submitted])
        assert entry["wtxid"] == child_one.hash.hex()
        _wait_for_broadcast(peer_wtxid_relay, {child_one.hash})
        assert node.rpc.call("getmempoolinfo")["unbroadcastcount"] == 0

        # testmempoolaccept refuses child one as already there, and child
        # two as the same non-witness data
        answer = node.rpc.call("testmempoolaccept", [[_raw(child_one)]])
        assert answer == [_refusal(child_one, "txn-already-in-mempool")]
        answer = node.rpc.call("testmempoolaccept", [[_raw(child_two)]])
        assert answer[0] == _refusal(child_two, "txn-same-nonwitness-data-in-mempool")

        # sendrawtransaction does not refuse child one a second time
        node.rpc.call("sendrawtransaction", [_raw(child_one)])

        peer_wtxid_relay_2 = _peer(node, stack)

        # nor child two, and it announces child one to the peer that has
        # not seen it, by the wtxid of the transaction its mempool holds
        node.rpc.call("sendrawtransaction", [_raw(child_two)])
        _wait_for_broadcast(peer_wtxid_relay_2, {child_one.hash})
        assert node.rpc.call("getmempoolinfo")["unbroadcastcount"] == 0
