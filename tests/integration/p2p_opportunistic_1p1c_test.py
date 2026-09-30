# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_opportunistic_1p1c`, a first batch, as bodies over either node.

Read from Core's `test/functional/p2p_opportunistic_1p1c.py`
(`0bd3d3dfa562`, 2026-07-24): a parent refused for its fee is taken
into the mempool with a child paying for both, the two evaluated
together as one parent and one child (1p1c) where one peer sent both.
Each of the checks below is one of Core's `test_*` methods, a body over
a fresh node:

- a parent refused for its fee, announced ahead of its child by an
  outbound peer (`Capability.TYPED_OUTBOUND`), is asked for again once
  the child arrives and taken in with it, and not asked of another
  outbound peer announcing it; once for a parent with a witness and
  once for one with none;
- a child arriving ahead of its parent is kept as an orphan and taken
  in with it;
- a child paying too little for both is refused with its parent, and
  neither is asked of another peer or taken in when the parent is sent
  again, while a later child paying enough is taken in with it; once for
  a parent with a witness and once for one with none;
- a child whose witness is invalid is not evaluated with its parent
  sent by another peer, and neither peer is dropped once the child's
  own peer sends that parent;
- a parent whose witness is invalid, sent by another peer, is refused
  alone and leaves the child kept, which is taken in once its own peer
  sends the valid parent;
- no parent of a child of two parents, each refused for its fee, is
  asked for;
- a child of two parents, one of them in the mempool, is taken in with
  the other;
- a parent and child spending the child of another such pair are taken
  in on top of it.

Every body asks for `Capability.ORPHANAGE` first. It starts its node
with `-maxmempool=5` (`Capability.MAXMEMPOOL`) and fills the mempool
with `mempool_util.fill_mempool`, so that its minimum fee rate stands
above the relay one, and mines its coins first (`Capability.MINE`,
`mini_wallet.MiniWallet`). Every body but the last moves the node's
clock (`Capability.CLOCK`) where Core's does, from the wall clock at its
start; the last, as Core's own, waits out the node's delays on the wall
clock.

Core builds a transaction with no witness, whose txid is its wtxid,
with a `MiniWalletMode.RAW_P2PK` wallet: here `_p2pk_coins` mines
coinbases paying `RAW_P2PK_SCRIPT_PUB_KEY` ahead of the wallet's own,
and `raw_p2pk_script_sig` (`mini_wallet.py`) signs every spend of one.

Core's `P2PInterface` records the latest `getdata` from its framework's
network thread, and asks for whatever the node announces. Here `_Conn`
does both on the test's own thread, where a wait reads the peer's
connection up to the `pong` of a ping round trip ahead of every poll.

What differs from Core's file besides:

- Core runs every check over one node, filled once, and ends each with
  its `cleanup`, which asserts the mempool's minimum fee rate still
  above the relay one; here each body starts a fresh node, fills its
  mempool and asserts none of that;
- Core gives each transaction its `create_tx_below_mempoolminfee` makes
  a sequence number of its own, so that no two of its checks make one
  txid on its one node; here every input's sequence number is zero;
- Core's invalid child is a `createrawtransaction` paying the node's own
  deterministic address, given a witness of garbage; here it is a
  self-transfer paying the same fee, its witness replaced by
  `malleated_to_invalid_witness`;
- Core's `RAW_P2PK` wallet signs a transaction's first input alone,
  drawing signatures until the scriptSig is of one fixed length; here
  every input is signed, under btclib's deterministic nonce, whatever
  the length;
- Core's node starts with `-inboundrelaypercent=100` besides, an option
  bitcoin/bitcoin@0bd3d3dfa562724e3dbc4cec2d4290e4561655cd adds and
  `v32.0rc1` is the first tag to carry; no body passes it, the checks
  connecting the most inbound peers being among those not ported yet.

Core's orphanage checks, `test_orphanage_dos_large` and
`test_orphanage_dos_many`, are not ported yet, for the size of this
batch alone.

`p2p_opportunistic_1p1c_bitcoind_test.py` and
`p2p_opportunistic_1p1c_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
import time
from contextlib import ExitStack
from typing import TYPE_CHECKING

from btclib.amount import sats_from_btc
from btclib.p2p import GetData, Inv, Inventory, InventoryType, Ping, Pong, TxPayload
from btclib.p2p.magic import magic_from_chain
from btclib.tx import OutPoint, Tx, TxIn, TxOut

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mempool_util import fill_mempool
from bitcoin_node_tests.mini_wallet import (
    RAW_P2PK_SCRIPT_PUB_KEY,
    MiniWallet,
    Utxo,
    build_next_block,
    raw_p2pk_script_sig,
)
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Listener, Peer
from bitcoin_node_tests.timeout_factor import scaled
from tests.integration.p2p_private_broadcast_test import malleated_to_invalid_witness

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message, Payload

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_package_is_taken_in_on_top_of_another",
    "a_rejected_parent_is_taken_in_only_with_a_child_paying_enough",
    "a_rejected_parent_is_taken_in_with_its_child",
    "a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough",
    "a_rejected_parent_with_no_witness_is_taken_in_with_its_child",
    "an_invalid_parent_from_another_peer_leaves_the_orphan",
    "an_orphan_is_taken_in_with_its_low_fee_parent",
    "an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool",
    "no_rejected_parent_of_a_two_parent_orphan_is_requested",
    "parent_and_child_are_evaluated_together_only_from_one_peer",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# Core's own constants (`test_framework/p2p.py`)
_NONPREF_PEER_TX_DELAY = 2
_TXID_RELAY_DELAY = 2

# Core's own `GETDATA_WAIT` (`p2p_opportunistic_1p1c.py`)
_GETDATA_WAIT = 60

# Core's own default wait, `P2PInterface`'s and `wait_until`'s
_WAIT = 60.0

# Core's own `FEERATE_1SAT_VB` (`p2p_opportunistic_1p1c.py`), in satoshis
# per 1000 virtual bytes
_FEERATE_1SAT_VB = 1000

# Core's own `DEFAULT_MIN_RELAY_TX_FEE` (`test_framework/mempool_util.py`),
# in satoshis per 1000 virtual bytes
_DEFAULT_MIN_RELAY_TX_FEE = 100

# Core's own virtual size of a `RAW_P2PK` self-transfer, which its
# `create_self_transfer` (`wallet.py`) prices the fee at
_P2PK_VSIZE = 168

# how far short of its coin Core's own invalid child pays, in satoshis:
# its `coin["value"] - Decimal("0.0001")`
_BAD_ORPHAN_FEE = 10_000

# what `fill_mempool` needs the node started with, as Core's own
# `extra_args` gives it
_MAXMEMPOOL = "-maxmempool=5"


class _Conn:
    """Core's own `P2PInterface`: a peer recording what the node asks of it.

    `Peer.wait_for` drops what it does not wait for, and Core's peer asks
    for whatever the node announces, so every wait here reads the
    connection itself and hands each message to `_handle` first.
    `last_getdata` is the items of the latest `getdata`, Core's
    `last_message["getdata"]`.

    :param peer: the connection, its handshake done.
    """

    def __init__(self, peer: Peer) -> None:
        self.peer = peer
        self.last_getdata: tuple[Inventory, ...] = ()

    def send(self, payload: Payload) -> None:
        """Core's own `send_without_ping`."""
        self.peer.send(payload)

    def _handle(self, message: Message) -> None:
        """Core's `on_getdata`, `on_inv` and `on_ping`."""
        if message.command == "ping":
            self.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "getdata":
            self.last_getdata = GetData.parse(message.payload).items
        elif message.command == "inv":
            wanted = [
                item for item in Inv.parse(message.payload).items if item.type_code
            ]
            if wanted:
                self.send(GetData(wanted))

    def sync_with_ping(self) -> None:
        """`Peer.sync_with_ping`'s barrier, every message read answered.

        :raises ConnectionError: the node closed the connection.
        :raises TimeoutError: no matching `pong` arrived within the wait.
        """
        nonce = secrets.randbelow(2**64 - 1) + 1
        self.send(Ping(0))
        self.send(Ping(nonce))
        deadline = time.monotonic() + scaled(_WAIT)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                err_msg = "no pong within the wait"
                raise TimeoutError(err_msg)
            message = self.peer.receive(timeout=remaining)
            self._handle(message)
            if message.command == "pong" and Pong.parse(message.payload).nonce == nonce:
                return

    def send_and_ping(self, payload: Payload) -> None:
        """Core's own `send_and_ping`: `send`, then `sync_with_ping`."""
        self.send(payload)
        self.sync_with_ping()

    def wait_for_getdata(self, hashes: list[bytes]) -> None:
        """Core's own `wait_for_getdata`: the last `getdata` names `hashes`.

        The peer is read up to a ping round trip ahead of every poll, as
        Core's `P2PInterface.wait_until` reads it under its lock.
        """

        def _served() -> bool:
            self.sync_with_ping()
            return [item.hash for item in self.last_getdata] == hashes

        wait_until(_served, timeout=_WAIT)

    def was_asked(self) -> bool:
        """Whether any `getdata` came, Core's `"getdata" in last_message`."""
        return "getdata" in self.peer.last_message


class _Clock:
    """Core's own mock time: `setmocktime` once, then `bumpmocktime`.

    :param node: the node whose clock this sets, to the wall clock now.
    """

    def __init__(self, node: NodeAdapter) -> None:
        self._node = node
        self._now = int(time.time())
        node.set_mock_time(self._now)

    def bump(self, seconds: int) -> None:
        """Core's own `bumpmocktime`: move the node's clock `seconds` on."""
        self._now += seconds
        self._node.set_mock_time(self._now)


def _inv(tx: Tx) -> Inv:
    """Core's own `msg_inv([CInv(t=MSG_WTX, h=tx.wtxid_int)])`."""
    return Inv([Inventory(InventoryType.MSG_WTX, tx.hash)])


def _tx(tx: Tx) -> TxPayload:
    """Core's own `msg_tx(tx)`, its witness serialized."""
    return TxPayload(tx, include_witness=True, check_validity=False)


def _inbound(stack: ExitStack, node: NodeAdapter) -> _Conn:
    """Core's own `add_p2p_connection(P2PInterface())`."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake()
    conn = _Conn(peer)
    conn.sync_with_ping()
    return conn


def _outbound(stack: ExitStack, node: NodeAdapter) -> _Conn:
    """Core's own `add_outbound_p2p_connection(P2PInterface(), ...)`.

    The connection type is `outbound-full-relay`, every one Core's file
    makes.
    """
    with Listener(_MAGIC) as listener:
        node.add_outbound_connection(listener.address, "outbound-full-relay")
        peer = stack.enter_context(listener.accept())
    peer.handshake()
    conn = _Conn(peer)
    conn.sync_with_ping()
    return conn


def _p2pk_coins(node: NodeAdapter, count: int) -> list[Utxo]:
    """Return `count` coins spent with no witness, mined on the node's tip.

    Core's own `generate(self.wallet_nonsegwit, count)`: `count` blocks,
    each built by `build_next_block` and submitted, whose coinbase pays
    `RAW_P2PK_SCRIPT_PUB_KEY`. Each coin is that coinbase's own output, a
    `Utxo` that `raw_p2pk_script_sig` spends rather than `MiniWallet`,
    immature until `fill_mempool` mines past it.

    :raises TypeError: `submitblock` answered anything but acceptance.
    """
    coins = []
    for _ in range(count):
        block = build_next_block(node, RAW_P2PK_SCRIPT_PUB_KEY)
        answer = node.rpc.call(
            "submitblock", [block.serialize(check_validity=False).hex()]
        )
        if answer is not None:
            err_msg = f"submitblock refused a coinbase paying P2PK: {answer!r}"
            raise TypeError(err_msg)
        coinbase = block.transactions[0]
        height = node.rpc.call("getblockcount")
        coins.append(
            Utxo(OutPoint(coinbase.id, 0), coinbase.vout[0].value, height, True)
        )
    return coins


def _p2pk_tx(coins: Sequence[Utxo], fee: int) -> Tx:
    """Return a signed tx spending `coins` into one `RAW_P2PK` output.

    Core's own `create_self_transfer_multi` in `RAW_P2PK` mode
    (`wallet.py`), paying `fee`.
    """
    tx = Tx(
        version=2,
        lock_time=0,
        vin=[TxIn(coin.outpoint) for coin in coins],
        vout=[TxOut(sum(coin.value for coin in coins) - fee, RAW_P2PK_SCRIPT_PUB_KEY)],
        check_validity=False,
    )
    for vin_i, tx_in in enumerate(tx.vin):
        tx_in.script_sig = raw_p2pk_script_sig(tx, vin_i)
    return tx


def _p2pk_self_transfer(coin: Utxo, fee_rate: int) -> Tx:
    """Core's own `create_self_transfer` of its `RAW_P2PK` wallet.

    Its fee: `fee_rate`, in satoshis per 1000 virtual bytes, over Core's
    own `RAW_P2PK` virtual size, rounded up.
    """
    return _p2pk_tx([coin], -(-fee_rate * _P2PK_VSIZE // 1000))


def _p2pk_new_utxo(tx: Tx) -> Utxo:
    """Core's own `new_utxo` of a `RAW_P2PK` transfer: its first output."""
    return Utxo(OutPoint(tx.id, 0), tx.vout[0].value, 0, False)


def _new_utxo(wallet: MiniWallet, tx: Tx) -> Utxo:
    """Core's own `new_utxo`: the first coin `tx` pays the wallet."""
    return wallet.new_utxos(tx)[0]


def _mempool(node: NodeAdapter) -> list[str]:
    """Return the node's own `getrawmempool`."""
    txids = node.rpc.call("getrawmempool")
    assert isinstance(txids, list)
    return txids


def _mempoolminfee(node: NodeAdapter) -> int:
    """Return `getmempoolinfo`'s `mempoolminfee`, in satoshis per 1000 vB."""
    return sats_from_btc(node.rpc.call("getmempoolinfo")["mempoolminfee"])


def _node(
    cluster: _Cluster,
    skip_counts: SkipCounts,
    *capabilities: Capability,
    coins: int,
    p2pk_coins: int = 0,
) -> tuple[NodeAdapter, MiniWallet, list[Utxo]]:
    """Return a fresh node whose mempool is full, a wallet, and P2PK coins.

    The node restarts with `-maxmempool=5`, then its coins are mined:
    `p2pk_coins` of them paying `RAW_P2PK_SCRIPT_PUB_KEY`, and `coins`
    to the wallet, all of which mature under the blocks `fill_mempool`
    mines before it fills the mempool.

    :param capabilities: what the body asks for besides
        `Capability.MAXMEMPOOL` and `Capability.MINE`, asked for after
        `Capability.ORPHANAGE`.
    """
    (node,) = cluster(1)
    for capability in (
        Capability.ORPHANAGE,
        *capabilities,
        Capability.MAXMEMPOOL,
        Capability.MINE,
    ):
        require(capability, node.capabilities, skip_counts)
    node.restart([_MAXMEMPOOL])
    p2pk = _p2pk_coins(node, p2pk_coins)
    wallet = MiniWallet(node)
    wallet.generate(coins)
    fill_mempool(node)
    wallet.resync()
    return node, wallet, p2pk


def _below_mempoolminfee(
    node: NodeAdapter, wallet: MiniWallet, utxo_to_spend: Utxo | None = None
) -> Tx:
    """Core's own `create_tx_below_mempoolminfee`, of its default wallet.

    A self-transfer at `_DEFAULT_MIN_RELAY_TX_FEE`, of a confirmed coin
    where `utxo_to_spend` is `None`, once the mempool's minimum fee rate
    is asserted above it.
    """
    assert _mempoolminfee(node) > _DEFAULT_MIN_RELAY_TX_FEE
    return wallet.create_self_transfer(
        fee_rate=_DEFAULT_MIN_RELAY_TX_FEE,
        utxo_to_spend=utxo_to_spend,
        confirmed_only=True,
    )


def _p2pk_below_mempoolminfee(node: NodeAdapter, coin: Utxo) -> Tx:
    """Core's own `create_tx_below_mempoolminfee`, of its `RAW_P2PK` wallet."""
    assert _mempoolminfee(node) > _DEFAULT_MIN_RELAY_TX_FEE
    return _p2pk_self_transfer(coin, _DEFAULT_MIN_RELAY_TX_FEE)


def _low_fee_parent(node: NodeAdapter, wallet: MiniWallet, p2pk: list[Utxo]) -> Tx:
    """Return `_p2pk_below_mempoolminfee`'s where `p2pk` holds a coin.

    `_below_mempoolminfee`'s otherwise.
    """
    if p2pk:
        return _p2pk_below_mempoolminfee(node, p2pk[0])
    return _below_mempoolminfee(node, wallet)


def _child(wallet: MiniWallet, parent: Tx, fee_rate: int, *, witness: bool) -> Tx:
    """Core's own `create_self_transfer` of `parent`'s new coin at `fee_rate`.

    Of the wallet `parent` is of: the default one where `witness`, the
    `RAW_P2PK` one otherwise.
    """
    if witness:
        return wallet.create_self_transfer(
            utxo_to_spend=_new_utxo(wallet, parent), fee_rate=fee_rate
        )
    return _p2pk_self_transfer(_p2pk_new_utxo(parent), fee_rate)


def _parent_then_child(
    cluster: _Cluster, skip_counts: SkipCounts, *, witness: bool
) -> None:
    """Core's own `test_basic_parent_then_child`, of either wallet."""
    node, wallet, p2pk = _node(
        cluster,
        skip_counts,
        Capability.TYPED_OUTBOUND,
        Capability.CLOCK,
        coins=1,
        p2pk_coins=0 if witness else 1,
    )
    clock = _Clock(node)
    low_fee_parent = _low_fee_parent(node, wallet, p2pk)
    high_fee_child = _child(
        wallet, low_fee_parent, 20 * _FEERATE_1SAT_VB, witness=witness
    )
    assert (low_fee_parent.id != low_fee_parent.hash) is witness
    with ExitStack() as stack:
        peer_sender = _outbound(stack, node)
        peer_ignored = _outbound(stack, node)

        # the parent is relayed first, and refused for its fee
        peer_sender.send_and_ping(_inv(low_fee_parent))
        peer_sender.wait_for_getdata([low_fee_parent.hash])
        peer_sender.send_and_ping(_tx(low_fee_parent))
        assert low_fee_parent.id.hex() not in _mempool(node)

        # another peer announcing it is not asked for it
        peer_ignored.send_and_ping(_inv(low_fee_parent))
        assert not peer_ignored.was_asked()

        # the child is relayed next, its input missing
        peer_sender.send_and_ping(_inv(high_fee_child))
        peer_sender.wait_for_getdata([high_fee_child.hash])
        peer_sender.send_and_ping(_tx(high_fee_child))

        # the parent is asked for by txid, refused as it was
        clock.bump(_TXID_RELAY_DELAY)
        peer_sender.wait_for_getdata([low_fee_parent.id])

        # and taken in with its child
        peer_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() in node_mempool
        assert high_fee_child.id.hex() in node_mempool


def a_rejected_parent_is_taken_in_with_its_child(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_basic_parent_then_child(self.wallet)`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _parent_then_child(cluster, skip_counts, witness=True)


def a_rejected_parent_with_no_witness_is_taken_in_with_its_child(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_basic_parent_then_child(self.wallet_nonsegwit)`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _parent_then_child(cluster, skip_counts, witness=False)


def an_orphan_is_taken_in_with_its_low_fee_parent(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_basic_child_then_parent`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, _ = _node(cluster, skip_counts, Capability.CLOCK, coins=1)
    clock = _Clock(node)
    low_fee_parent = _below_mempoolminfee(node, wallet)
    high_fee_child = _child(wallet, low_fee_parent, 20 * _FEERATE_1SAT_VB, witness=True)
    with ExitStack() as stack:
        peer_sender = _inbound(stack, node)

        # the child arrives first, its input missing
        peer_sender.send_and_ping(_inv(high_fee_child))
        clock.bump(_NONPREF_PEER_TX_DELAY)
        peer_sender.wait_for_getdata([high_fee_child.hash])
        peer_sender.send_and_ping(_tx(high_fee_child))

        # the parent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer_sender.wait_for_getdata([low_fee_parent.id])

        # and taken in with its child
        peer_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() in node_mempool
        assert high_fee_child.id.hex() in node_mempool


def _low_and_high_child(
    cluster: _Cluster, skip_counts: SkipCounts, *, witness: bool
) -> None:
    """Core's own `test_low_and_high_child`, of either wallet."""
    node, wallet, p2pk = _node(
        cluster,
        skip_counts,
        Capability.TYPED_OUTBOUND,
        Capability.CLOCK,
        coins=1,
        p2pk_coins=0 if witness else 1,
    )
    clock = _Clock(node)
    low_fee_parent = _low_fee_parent(node, wallet, p2pk)
    # above the mempool's minimum fee rate, too little to pay for the parent
    med_fee_child = _child(
        wallet, low_fee_parent, _mempoolminfee(node), witness=witness
    )
    high_fee_child = _child(
        wallet, low_fee_parent, 999 * _FEERATE_1SAT_VB, witness=witness
    )
    with ExitStack() as stack:
        peer_sender = _outbound(stack, node)
        peer_ignored = _outbound(stack, node)

        # the parent is refused for its fee
        peer_sender.send_and_ping(_inv(low_fee_parent))
        peer_sender.wait_for_getdata([low_fee_parent.hash])
        peer_sender.send_and_ping(_tx(low_fee_parent))
        assert low_fee_parent.id.hex() not in _mempool(node)

        # another peer announcing it is not asked for it
        peer_ignored.send_and_ping(_inv(low_fee_parent))
        assert not peer_ignored.was_asked()

        # the child paying too little arrives, its input missing
        peer_sender.send_and_ping(_inv(med_fee_child))
        peer_sender.wait_for_getdata([med_fee_child.hash])
        peer_sender.send_and_ping(_tx(med_fee_child))

        # the parent is asked for by txid
        clock.bump(_TXID_RELAY_DELAY)
        peer_sender.wait_for_getdata([low_fee_parent.id])

        # the two are refused together, for their fee
        peer_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() not in node_mempool
        assert med_fee_child.id.hex() not in node_mempool

        # another peer announcing that child is not asked for it
        peer_ignored.send_and_ping(_inv(med_fee_child))
        assert not peer_ignored.was_asked()

        # the parent sent again, by either peer, is not taken in
        peer_sender.send_and_ping(_tx(low_fee_parent))
        peer_ignored.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() not in node_mempool
        assert med_fee_child.id.hex() not in node_mempool

        # the child paying enough arrives, its input missing
        peer_sender.send_and_ping(_inv(high_fee_child))
        peer_sender.wait_for_getdata([high_fee_child.hash])
        peer_sender.send_and_ping(_tx(high_fee_child))

        # the parent is asked for again, refused alone and with a child as
        # it was, lest the child be censored
        clock.bump(_TXID_RELAY_DELAY)
        peer_sender.wait_for_getdata([low_fee_parent.id])

        # and taken in with that child, and not the other
        peer_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() in node_mempool
        assert high_fee_child.id.hex() in node_mempool
        assert med_fee_child.id.hex() not in node_mempool


def a_rejected_parent_is_taken_in_only_with_a_child_paying_enough(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_low_and_high_child(self.wallet)`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _low_and_high_child(cluster, skip_counts, witness=True)


def a_rejected_parent_with_no_witness_is_taken_in_only_with_a_child_paying_enough(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_low_and_high_child(self.wallet_nonsegwit)`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    _low_and_high_child(cluster, skip_counts, witness=False)


def parent_and_child_are_evaluated_together_only_from_one_peer(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_consensus_failure`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, _ = _node(cluster, skip_counts, Capability.CLOCK, coins=1)
    clock = _Clock(node)
    low_fee_parent = _below_mempoolminfee(node, wallet)
    # a child spending the parent, its witness invalid
    tx_orphan_bad_wit = malleated_to_invalid_witness(
        wallet.create_self_transfer(
            utxo_to_spend=_new_utxo(wallet, low_fee_parent), fee=_BAD_ORPHAN_FEE
        )
    )
    with ExitStack() as stack:
        bad_orphan_sender = _inbound(stack, node)
        parent_sender = _inbound(stack, node)

        # the child arrives first, its input missing
        bad_orphan_sender.send_and_ping(_inv(tx_orphan_bad_wit))
        clock.bump(_NONPREF_PEER_TX_DELAY)
        bad_orphan_sender.wait_for_getdata([tx_orphan_bad_wit.hash])
        bad_orphan_sender.send_and_ping(_tx(tx_orphan_bad_wit))

        # the parent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        bad_orphan_sender.wait_for_getdata([low_fee_parent.id])

        # another peer sends it, and the two are not evaluated together
        parent_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() not in node_mempool
        assert tx_orphan_bad_wit.id.hex() not in node_mempool

        # the child's own peer sends it, and neither peer is dropped
        bad_orphan_sender.send_and_ping(_tx(low_fee_parent))
        bad_orphan_sender.sync_with_ping()
        parent_sender.sync_with_ping()


def an_invalid_parent_from_another_peer_leaves_the_orphan(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_parent_consensus_failure`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, _ = _node(cluster, skip_counts, Capability.CLOCK, coins=1)
    clock = _Clock(node)
    low_fee_parent = _below_mempoolminfee(node, wallet)
    high_fee_child = _child(
        wallet, low_fee_parent, 999 * _FEERATE_1SAT_VB, witness=True
    )
    # the parent, its witness invalid
    tx_parent_bad_wit = malleated_to_invalid_witness(low_fee_parent)
    with ExitStack() as stack:
        package_sender = _inbound(stack, node)
        fake_parent_sender = _inbound(stack, node)

        # the child arrives first, its input missing
        package_sender.send_and_ping(_inv(high_fee_child))
        clock.bump(_NONPREF_PEER_TX_DELAY)
        package_sender.wait_for_getdata([high_fee_child.hash])
        package_sender.send_and_ping(_tx(high_fee_child))

        # the parent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        package_sender.wait_for_getdata([tx_parent_bad_wit.id])

        # another peer sends the invalid one, refused alone for its fee
        fake_parent_sender.send_and_ping(_tx(tx_parent_bad_wit))
        node_mempool = _mempool(node)
        assert tx_parent_bad_wit.id.hex() not in node_mempool
        assert high_fee_child.id.hex() not in node_mempool

        # the child is kept, and taken in once its own peer sends the parent
        package_sender.send_and_ping(_inv(low_fee_parent))
        clock.bump(_NONPREF_PEER_TX_DELAY)
        package_sender.wait_for_getdata([low_fee_parent.hash])
        package_sender.send_and_ping(_tx(low_fee_parent))
        node_mempool = _mempool(node)
        assert low_fee_parent.id.hex() in node_mempool
        assert high_fee_child.id.hex() in node_mempool


def no_rejected_parent_of_a_two_parent_orphan_is_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_multiple_parents`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, _, p2pk = _node(
        cluster,
        skip_counts,
        Capability.TYPED_OUTBOUND,
        Capability.CLOCK,
        coins=0,
        p2pk_coins=2,
    )
    clock = _Clock(node)
    # two parents with no witness, each under the mempool's minimum fee rate
    parent_low_1 = _p2pk_below_mempoolminfee(node, p2pk[0])
    parent_low_2 = _p2pk_below_mempoolminfee(node, p2pk[1])
    child_bumping = _p2pk_tx(
        [_p2pk_new_utxo(parent_low_1), _p2pk_new_utxo(parent_low_2)],
        999 * parent_low_1.vsize,
    )
    with ExitStack() as stack:
        peer_sender = _outbound(stack, node)

        # both parents are sent unasked, and refused for their fee
        peer_sender.send_and_ping(_tx(parent_low_1))
        peer_sender.send_and_ping(_tx(parent_low_2))
        node_mempool = _mempool(node)
        assert parent_low_1.id.hex() not in node_mempool
        assert parent_low_2.id.hex() not in node_mempool

        # the child is sent, and neither parent asked for
        peer_sender.send_and_ping(_tx(child_bumping))
        clock.bump(_GETDATA_WAIT)
        peer_sender.sync_with_ping()
        assert not peer_sender.was_asked()


def an_orphan_is_taken_in_with_one_parent_beside_another_in_the_mempool(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_other_parent_in_mempool`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, _ = _node(
        cluster, skip_counts, Capability.TYPED_OUTBOUND, Capability.CLOCK, coins=2
    )
    clock = _Clock(node)
    # a grandparent taken in by itself
    grandparent_high = wallet.create_self_transfer(
        fee_rate=10 * _FEERATE_1SAT_VB, confirmed_only=True
    )
    # a parent needing its child to pay for it
    parent_low = _below_mempoolminfee(node, wallet, _new_utxo(wallet, grandparent_high))
    # a parent taken in by itself, ahead of the child
    parent_high = wallet.create_self_transfer(
        fee_rate=10 * _FEERATE_1SAT_VB, confirmed_only=True
    )
    child = wallet.create_self_transfer_multi(
        utxos_to_spend=[_new_utxo(wallet, parent_high), _new_utxo(wallet, parent_low)],
        fee_per_output=999 * parent_low.vsize,
    )
    with ExitStack() as stack:
        peer_sender = _outbound(stack, node)

        # the grandparent and the first parent are taken in
        peer_sender.send_and_ping(_tx(grandparent_high))
        assert grandparent_high.id.hex() in _mempool(node)
        peer_sender.send_and_ping(_tx(parent_high))
        assert parent_high.id.hex() in _mempool(node)

        # the child is kept as an orphan, and the other parent asked for
        peer_sender.send_and_ping(_tx(child))
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer_sender.wait_for_getdata([parent_low.id])
        peer_sender.send_and_ping(_tx(parent_low))

        node_mempool = _mempool(node)
        assert grandparent_high.id.hex() in node_mempool
        assert parent_high.id.hex() in node_mempool
        assert parent_low.id.hex() in node_mempool
        assert child.id.hex() in node_mempool


def a_package_is_taken_in_on_top_of_another(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_1p1c_on_1p1c`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, _ = _node(cluster, skip_counts, coins=1)
    # two generations of a parent and a child, the younger spending the older
    low_fee_great_grandparent = _below_mempoolminfee(node, wallet)
    high_fee_grandparent = _child(
        wallet, low_fee_great_grandparent, 20 * _FEERATE_1SAT_VB, witness=True
    )
    low_fee_parent = _below_mempoolminfee(
        node, wallet, _new_utxo(wallet, high_fee_grandparent)
    )
    high_fee_child = _child(wallet, low_fee_parent, 20 * _FEERATE_1SAT_VB, witness=True)
    with ExitStack() as stack:
        peer_sender = _inbound(stack, node)

        # the pair spending the confirmed coin first, then the other
        for parent_relative, child_relative in (
            (low_fee_great_grandparent, high_fee_grandparent),
            (low_fee_parent, high_fee_child),
        ):
            # the child arrives first, its input missing
            peer_sender.send_and_ping(_inv(child_relative))
            peer_sender.wait_for_getdata([child_relative.hash])
            peer_sender.send_and_ping(_tx(child_relative))

            # the parent is asked for by txid, and taken in with the child
            peer_sender.wait_for_getdata([parent_relative.id])
            peer_sender.send_and_ping(_tx(parent_relative))

        node_mempool = _mempool(node)
        assert low_fee_great_grandparent.id.hex() in node_mempool
        assert high_fee_grandparent.id.hex() in node_mempool
        assert low_fee_parent.id.hex() in node_mempool
        assert high_fee_child.id.hex() in node_mempool
        entry = node.rpc.call("getmempoolentry", [low_fee_great_grandparent.id.hex()])
        assert entry["descendantcount"] == 4
