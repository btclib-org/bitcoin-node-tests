# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_orphan_handling`, as bodies over either node.

Read from Core's `test/functional/p2p_orphan_handling.py` (`9cc7dc50bdc9`,
2026-08-17): which peers a node asks for the missing parents of an
orphan it keeps (`Capability.ORPHANAGE`), and when. Each of the checks
below is one of Core's `test_*` methods, a body over a fresh node:

- a parent that arrives while the request for it waits is not asked
  for, and one that does not arrive is;
- the child of a parent with no witness refused for its size is refused
  too and its parents asked for by nobody, while a parent refused for
  its fee, or with its witness stripped, is asked for again, the second
  taken in under its witness;
- a parent confirmed ahead of a block taken off the tip
  (`Capability.INVALIDATE_BLOCK`) is asked for beside a missing one, and
  neither one confirmed since nor one in the mempool is, the orphan
  outliving a `notfound` for the first;
- a parent whose request is in flight, to another peer or for another
  orphan, is not asked for again, the first until that request expires;
- a parent kept as an orphan is not asked for by its orphan child;
- an orphan is taken into the mempool once a block confirms its parent;
- the descendants of a parent with no witness refused for its size are
  refused too, and the child is not asked for again, as a missing parent
  or announced by its txid;
- a transaction sharing an orphan's txid and not its witness is kept
  beside it, and the one whose witness is valid is taken in once the
  parent arrives (`Capability.DEBUG_LOG` for the node's own
  `missingorspent`);
- a parent already kept as an orphan under another witness is asked for
  again;
- a transaction announced by the txid of an orphan is asked for;
- the parents of an orphan are asked of an outbound peer announcing it
  ahead of an inbound one (`Capability.TYPED_OUTBOUND`), and of the
  inbound one once that request expires;
- every peer announcing an orphan, before it arrives or after, is asked
  for its parents in turn, a peer that disconnects dropping out;
- a parent that leaves the mempool while its orphan waits is asked for
  beside the parent still missing;
- an ancestor package of the largest size, its first transaction missing,
  is kept whole while other peers fill the orphanage with large orphans,
  and taken in once that transaction arrives.

Every body moves the node's clock (`Capability.CLOCK`) where Core's
does, from the wall clock at its start, and mines its coins first
(`Capability.MINE`, `mini_wallet.MiniWallet`), which also leaves initial
block download, where a node ignores every transaction announced to it.

Core builds a transaction with no witness, whose txid is its wtxid,
with a `MiniWalletMode.RAW_P2PK` wallet: here `_p2pk_coins` mines
coinbases paying `RAW_P2PK_SCRIPT_PUB_KEY` ahead of the wallet's own, so
that they mature with its coins, and `raw_p2pk_script_sig`
(`mini_wallet.py`) signs every spend of one.

Core's `PeerTxRelayer` records each `getdata` from its framework's
network thread, and its `P2PInterface` asks for whatever the node
announces. Here `_Conn` does both on the test's own thread, where a
wait reads the peer's connection: a wait for a request reads the peer
up to the `pong` of a ping round trip ahead of every poll, and a check
that a peer was not asked reads it up to that `pong` once, as Core's
own `assert_never_requested` does. A peer announcing by txid is
`Peer.handshake(wtxidrelay=False)`.

What differs from Core's file besides:

- Core runs every check over one node and ends each with its `cleanup`,
  which mines the node's mempool into a block, asserts the mempool and
  the orphanage empty and restarts the node; here each body starts a
  fresh node and asserts none of that;
- Core confirms the parent of its reconsideration check with
  `generateblock`; here `MiniWallet.generate` carries it;
- Core's reorg calls `preciousblock` on the block `invalidateblock` has
  just marked invalid, which leaves the tip where `invalidateblock` put
  it; here the body asserts that tip instead;
- Core's `syncwithvalidationinterfacequeue`, and the one its `generate`
  ends in, are bitcoind's own RPC, so `_sync_validation_queue` calls it
  on bitcoind alone: the node empties and fills its filter of recently
  confirmed transactions on events queued behind the block
  (`src/validationinterface.cpp`);
- Core's harness starts every node with a `peertimeout` (`write_config`,
  `test_framework/util.py`) and this port passes none: no body moves the
  node's clock as far as `TIMEOUT_INTERVAL` (`src/net.h`);
- Core's `RAW_P2PK` wallet signs a transaction's first input alone, and
  ahead of the output `target_vsize` pads it with; here every input is
  signed, after that output, a padded transaction paying a satoshi more
  fee for each signing retried to reach its size;
- Core's inherit-rejection check hands `assert_never_requested` a hex
  string where a requested hash is an integer, so none of those checks
  can fail; here each reads the hash, once the node's clock has moved
  past the delay a parent's request waits. The refused parent's check
  reads the latest `getdata` its peer had, which names the child: that
  peer was asked for the parent when it relayed it, under the wtxid that
  is also its txid.

An orphan is taken into the mempool once a block confirms its parent
past the pinned release, from
bitcoin/bitcoin@9cc7dc50bdc9867d079ab7a111d39487a4566767, which `v32.0rc1`
is the first tag to carry: a bitcoind whose `getnetworkinfo` `version`
reads older than that
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35))
keeps the orphan, which is asserted there instead. A `master` build
between that change's merge and the version's move to `32.99` reads
older and takes it in all the same, the constant's own comment having
the commits.

`p2p_orphan_handling_bitcoind_test.py` and
`p2p_orphan_handling_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
import time
from contextlib import ExitStack
from typing import TYPE_CHECKING

from btclib import var_int
from btclib.p2p import (
    GetData,
    Inv,
    Inventory,
    InventoryType,
    NotFound,
    Ping,
    Pong,
    TxPayload,
)
from btclib.p2p.magic import magic_from_chain
from btclib.script.script import serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import (
    DEFAULT_FEE_RATE,
    FEE,
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
from tests.integration.rpc_orphans_test import in_orphanage

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message, Payload

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_maximal_ancestor_package_is_protected_in_the_orphanage",
    "a_parent_gone_missing_is_requested",
    "a_parent_kept_as_an_orphan_is_not_requested",
    "a_parent_of_the_same_txid_is_requested_again",
    "a_rejected_parent_is_requested_only_under_another_witness",
    "an_inv_by_an_orphan_txid_is_requested",
    "an_orphan_is_reconsidered_once_its_parent_is_mined",
    "an_orphan_of_the_same_txid_is_kept_too",
    "an_outbound_announcer_is_asked_for_parents_first",
    "descendants_of_a_rejected_parent_are_rejected_too",
    "every_announcer_is_asked_for_parents",
    "parents_already_requested_are_not_requested_again",
    "parents_arriving_during_the_delay_are_not_requested",
    "parents_not_recently_confirmed_are_requested",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# Core's own constants (`test_framework/p2p.py`)
_NONPREF_PEER_TX_DELAY = 2
_TXID_RELAY_DELAY = 2
_OVERLOADED_PEER_TX_DELAY = 2
_GETDATA_TX_INTERVAL = 60

# Core's own `TXREQUEST_TIME_SKIP` (`p2p_orphan_handling.py`)
_TXREQUEST_TIME_SKIP = (
    _NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY + _OVERLOADED_PEER_TX_DELAY + 1
)

# Core's own default wait, `P2PInterface`'s and `wait_until`'s, and the
# one its `wait_for_parent_requests` passes
_WAIT = 60.0
_PARENT_REQUESTS_WAIT = 10.0

# Core's own `FEE_INCREMENT` (`p2p_orphan_handling.py`), in satoshis
_FEE_INCREMENT = 2400

# Core's own `MAX_STANDARD_TX_WEIGHT` (`test_framework/blocktools.py`)
_MAX_STANDARD_TX_WEIGHT = 400_000

# a virtual size one past what `_MAX_STANDARD_TX_WEIGHT` admits, Core's own
# `target_vsize=int(MAX_STANDARD_TX_WEIGHT / 4) + 1`
_OVERLY_LARGE_VSIZE = _MAX_STANDARD_TX_WEIGHT // 4 + 1

# Core's own virtual size of a `RAW_P2PK` self-transfer, which its
# `create_self_transfer` (`wallet.py`) prices the fee at
_P2PK_VSIZE = 168

# how many signings `_p2pk_tx` tries before it raises rather than keeps
# looking for one whose size matches `target_vsize`
_SIGNING_ATTEMPTS = 64

# Core's own `CLIENT_VERSION` (`src/clientversion.h`), the running build's
# own `getnetworkinfo` `version`, at or past which an orphan is taken into
# the mempool once a block confirms its parent: `v32.0`'s, `v32.0rc1`
# being the first tag carrying the change. A known limit: a `master` build
# from its merge (`681b429393`, 2026-08-18) until the version moved to
# `32.99` (`f3fec67c3e`, 2026-09-11) reports `319900` and takes it in all
# the same, so this test fails against such a build
_RECONSIDERS_ON_BLOCK_VERSION = 320000

# Core's own `DEFAULT_ANCESTOR_LIMIT` (`test_framework/messages.py`)
_DEFAULT_ANCESTOR_LIMIT = 25

# Core's own `test_maximal_package_protected`: the large orphans it makes,
# the ones among them each sent by a peer of its own, and the virtual size
# its ancestor package adds up to
_LARGE_ORPHANS = 60
_INDIVIDUAL_DOSERS = 20
_MAXIMAL_PACKAGE_VSIZE = 101_000

# the size of the one witness item Core's own `create_large_orphan`
# (`test_framework/mempool_util.py`) spends its input with
_LARGE_ORPHAN_WITNESS_SIZE = 390_000

_TX_TYPES = (InventoryType.MSG_TX, InventoryType.MSG_WTX)

# the commands Core's own `assert_no_immediate_response` reads
_RESPONSES = ("getdata", "inv", "tx")


class _Conn:
    """Core's own `PeerTxRelayer`: a peer recording what the node asks of it.

    `Peer.wait_for` drops what it does not wait for, and Core's peer asks
    for whatever the node announces, so every wait here reads the
    connection itself and hands each message to `_handle` first.
    `last_getdata` is the items of the latest `getdata`, Core's
    `last_message["getdata"]`; `requested` the hash of every item any
    `getdata` named, Core's `getdata_received`; `tx_invs` the hash of every
    transaction an `inv` announced, Core's `P2PTxInvStore.get_invs`.

    :param peer: the connection, its handshake done.
    """

    def __init__(self, peer: Peer) -> None:
        self.peer = peer
        self.last_getdata: tuple[Inventory, ...] = ()
        self.requested: set[bytes] = set()
        self.tx_invs: list[bytes] = []

    def send(self, payload: Payload) -> None:
        """Core's own `send_without_ping`."""
        self.peer.send(payload)

    def _handle(self, message: Message) -> None:
        """Core's `on_getdata`, `on_inv`, `P2PTxInvStore`'s, and `on_ping`."""
        if message.command == "ping":
            self.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "getdata":
            self.last_getdata = GetData.parse(message.payload).items
            self.requested.update(item.hash for item in self.last_getdata)
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            self.tx_invs += [item.hash for item in items if item.type_code in _TX_TYPES]
            wanted = [item for item in items if item.type_code]
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

    def _wait_until(self, predicate: Callable[[], bool], *, timeout: float) -> None:
        """Core's own `P2PInterface.wait_until`, the peer read before a poll."""

        def _served() -> bool:
            self.sync_with_ping()
            return predicate()

        wait_until(_served, timeout=timeout)

    def wait_for_getdata(self, hashes: list[bytes]) -> None:
        """Core's own `wait_for_getdata`: the last `getdata` names `hashes`."""
        self._wait_until(
            lambda: [item.hash for item in self.last_getdata] == hashes,
            timeout=_WAIT,
        )

    def wait_for_parent_requests(self, txids: list[bytes]) -> None:
        """Core's own `wait_for_parent_requests`.

        The latest `getdata` asks for exactly `txids`, each as a
        `MSG_WITNESS_TX`.
        """

        def _requested() -> bool:
            items = self.last_getdata
            return len(items) == len(txids) and all(
                item.type_code == InventoryType.MSG_WITNESS_TX and item.hash in txids
                for item in items
            )

        self._wait_until(_requested, timeout=_PARENT_REQUESTS_WAIT)

    def wait_for_request(self, txhash: bytes) -> None:
        """Wait for the latest `getdata` to name `txhash`, among any others.

        Core's `test_maximal_package_protected` waits so on its peer, where
        `wait_for_getdata` asks for the latest to name exactly its hashes.
        """
        self._wait_until(
            lambda: txhash in [item.hash for item in self.last_getdata],
            timeout=_WAIT,
        )

    def assert_no_immediate_response(self, payload: Payload) -> None:
        """Core's own `assert_no_immediate_response`.

        No `getdata`, `inv` or `tx` answers `payload` ahead of the `pong`
        of a ping round trip: the latest of each is the one there was
        before.
        """
        before = {
            command: self.peer.last_message.get(command) for command in _RESPONSES
        }
        self.send_and_ping(payload)
        for command in _RESPONSES:
            assert self.peer.last_message.get(command) == before[command]

    def assert_never_requested(self, txhash: bytes) -> None:
        """Core's own `assert_never_requested`, after a ping round trip."""
        self.sync_with_ping()
        assert txhash not in self.requested


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


def _inv(inv_type: InventoryType, value: bytes) -> Inv:
    """Core's own `msg_inv([CInv(t=inv_type, h=value)])`."""
    return Inv([Inventory(inv_type, value)])


def _tx(tx: Tx) -> TxPayload:
    """Core's own `msg_tx(tx)`, its witness serialized."""
    return TxPayload(tx, include_witness=True, check_validity=False)


def _inbound(stack: ExitStack, node: NodeAdapter, *, wtxidrelay: bool = True) -> _Conn:
    """Core's own `add_p2p_connection(PeerTxRelayer(wtxidrelay=wtxidrelay))`."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake(wtxidrelay=wtxidrelay)
    conn = _Conn(peer)
    conn.sync_with_ping()
    return conn


def _outbound(stack: ExitStack, node: NodeAdapter) -> _Conn:
    """Core's own `add_outbound_p2p_connection(PeerTxRelayer(), ...)`.

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


def _fresh_node(
    cluster: _Cluster, skip_counts: SkipCounts, *capabilities: Capability
) -> NodeAdapter:
    """Return a fresh node, every capability the body asks for declared.

    :param capabilities: what the body asks for besides `Capability.CLOCK`
        and `Capability.MINE`, asked for after `Capability.ORPHANAGE`.
    """
    (node,) = cluster(1)
    for capability in (Capability.ORPHANAGE, *capabilities):
        require(capability, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    return node


def _wallet(node: NodeAdapter, coins: int) -> tuple[MiniWallet, _Clock]:
    """Return a wallet holding `coins` matured coins, and the node's clock.

    Every coinbase mined ahead of this call matures with them.
    """
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + coins)
    return wallet, _Clock(node)


def _node(
    cluster: _Cluster, skip_counts: SkipCounts, coins: int, *capabilities: Capability
) -> tuple[NodeAdapter, MiniWallet, _Clock]:
    """Return a fresh node, a wallet holding `coins` coins, and its clock.

    :param coins: the matured coins the body spends.
    :param capabilities: `_fresh_node`'s own.
    """
    node = _fresh_node(cluster, skip_counts, *capabilities)
    return node, *_wallet(node, coins)


def _p2pk_coins(node: NodeAdapter, count: int) -> list[Utxo]:
    """Return `count` coins spent with no witness, mined on the node's tip.

    Core's own `generate(self.wallet_nonsegwit, count)`: `count` blocks,
    each built by `build_next_block` and submitted, whose coinbase pays
    `RAW_P2PK_SCRIPT_PUB_KEY`. Each coin is that coinbase's own output, a
    `Utxo` that `raw_p2pk_script_sig` spends rather than `MiniWallet`,
    immature until `_wallet` mines past it.

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


def _p2pk_tx(coins: Sequence[Utxo], fee: int, target_vsize: int) -> Tx:
    """Return a signed tx spending `coins` into one `RAW_P2PK` output.

    Core's own `create_self_transfer_multi` in `RAW_P2PK` mode
    (`wallet.py`), paying `fee` and padded, where `target_vsize` is
    nonzero, by an `OP_RETURN` output of `OP_1` opcodes to exactly that
    many virtual bytes, as Core's own `bulk_vout`
    (`test_framework/script_util.py`) pads it. Every input is signed after
    the padding, which is sized for the signatures of the attempt before.
    A signature's length moves with what it signs, and btclib's nonce is
    deterministic, so each padding after the first also takes one more
    satoshi off the output, for a different transaction to sign, where
    Core's own `sign_tx` draws a random nonce until the length is fixed.

    :raises RuntimeError: no attempt within `_SIGNING_ATTEMPTS` reached
        `target_vsize`.
    """
    value = sum(coin.value for coin in coins) - fee
    tx = Tx(
        version=2,
        lock_time=0,
        vin=[TxIn(coin.outpoint) for coin in coins],
        vout=[TxOut(value, RAW_P2PK_SCRIPT_PUB_KEY)],
        check_validity=False,
    )
    for attempt in range(_SIGNING_ATTEMPTS):
        for vin_i, tx_in in enumerate(tx.vin):
            tx_in.script_sig = raw_p2pk_script_sig(tx, vin_i)
        if not target_vsize or tx.vsize == target_vsize:
            return tx
        # the padding output: its value, its script's length prefix, and
        # the `OP_RETURN` opcode leave the rest to `OP_1` opcodes
        del tx.vout[1:]
        deficit = target_vsize - tx.vsize - 8
        length = next(
            deficit - size
            for size in (1, 3, 5)
            if len(var_int.serialize(deficit - size)) == size
        )
        padding = serialize(["OP_RETURN", *(["OP_1"] * (length - 1))])
        tx.vout[0] = TxOut(value - attempt, RAW_P2PK_SCRIPT_PUB_KEY)
        tx.vout.append(TxOut(0, ScriptPubKey(padding, check_validity=False)))
    err_msg = f"no signature reached target_vsize {target_vsize}"
    raise RuntimeError(err_msg)


def _p2pk_self_transfer(coin: Utxo, *, target_vsize: int = 0) -> Tx:
    """Core's own `create_self_transfer` of its `RAW_P2PK` wallet.

    Its fee: `DEFAULT_FEE_RATE` over Core's own `RAW_P2PK` virtual size,
    or over `target_vsize` where nonzero, rounded up, plus a satoshi for
    each signing `_p2pk_tx` retries to reach that size.
    """
    fee = -(-DEFAULT_FEE_RATE * (target_vsize or _P2PK_VSIZE) // 1000)
    return _p2pk_tx([coin], fee, target_vsize)


def _p2pk_self_transfer_multi(coins: Sequence[Utxo]) -> Tx:
    """Core's own `create_self_transfer_multi` of its `RAW_P2PK` wallet."""
    return _p2pk_tx(coins, FEE, 0)


def _p2pk_new_utxo(tx: Tx) -> Utxo:
    """Core's own `new_utxo` of a `RAW_P2PK` transfer: its first output."""
    return Utxo(OutPoint(tx.id, 0), tx.vout[0].value, 0, False)


def _large_orphan() -> Tx:
    """Core's own `create_large_orphan` (`test_framework/mempool_util.py`).

    Its one input spends an outpoint of a random txid, at a random index
    past the first, under a witness of one `_LARGE_ORPHAN_WITNESS_SIZE`
    item; its one output pays a hundred satoshis to an `OP_RETURN` of
    twenty bytes.
    """
    prev_out = OutPoint(
        secrets.token_bytes(32), secrets.randbelow(99) + 1, check_validity=False
    )
    witness = Witness([b"X" * _LARGE_ORPHAN_WITNESS_SIZE])
    script = serialize(["OP_RETURN", b"a" * 20])
    return Tx(
        version=2,
        lock_time=0,
        vin=[TxIn(prev_out, script_witness=witness)],
        vout=[TxOut(100, ScriptPubKey(script, check_validity=False))],
        check_validity=False,
    )


def _orphans(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `getorphantxs` at verbosity 2, each orphan and its announcers."""
    orphanage = node.rpc.call("getorphantxs", {"verbosity": 2})
    assert isinstance(orphanage, list)
    return orphanage


def _announcers(node: NodeAdapter) -> int:
    """Return how many peers announced the one orphan the node keeps."""
    announcers = _orphans(node)[0]["from"]
    assert isinstance(announcers, list)
    return len(announcers)


def _mempool(node: NodeAdapter) -> list[str]:
    """Return the node's own `getrawmempool`."""
    txids = node.rpc.call("getrawmempool")
    assert isinstance(txids, list)
    return txids


def _mempool_wtxid(node: NodeAdapter, tx: Tx) -> object:
    """Return the wtxid the node's mempool holds `tx`'s txid under."""
    return node.rpc.call("getmempoolentry", [tx.id.hex()])["wtxid"]


def _send_raw(node: NodeAdapter, tx: Tx) -> None:
    """Core's own `node.sendrawtransaction(tx["hex"])`."""
    node.rpc.call("sendrawtransaction", [tx.serialize(True).hex()])


def _new_utxo(wallet: MiniWallet, tx: Tx) -> Utxo:
    """Core's own `new_utxo`: the first coin `tx` pays the wallet."""
    return wallet.new_utxos(tx)[0]


def _ancestor_count(node: NodeAdapter, tx: Tx) -> object:
    """Return `getmempoolentry`'s own `ancestorcount` for `tx`."""
    return node.rpc.call("getmempoolentry", [tx.id.hex()])["ancestorcount"]


def _sync_validation_queue(node: NodeAdapter) -> None:
    """Core's own `syncwithvalidationinterfacequeue`, on bitcoind alone."""
    if isinstance(node, BitcoindAdapter):
        node.rpc.call("syncwithvalidationinterfacequeue")


def _relay_transaction(conn: _Conn, clock: _Clock, tx: Tx) -> None:
    """Core's own `relay_transaction`: announced by wtxid, asked for, sent."""
    conn.send_and_ping(_inv(InventoryType.MSG_WTX, tx.hash))
    clock.bump(_TXREQUEST_TIME_SKIP)
    conn.wait_for_getdata([tx.hash])
    conn.send_and_ping(_tx(tx))


def _parent_and_child(wallet: MiniWallet) -> tuple[Tx, Tx]:
    """Core's own `create_parent_and_child`: an unsent parent and its child."""
    parent = wallet.create_self_transfer()
    child = wallet.create_self_transfer(utxo_to_spend=_new_utxo(wallet, parent))
    return parent, child


def _reconsiders_on_block(node: NodeAdapter) -> bool:
    """Whether `node` takes an orphan in once a block confirms its parent.

    Core's own claim for every node, bitcoind before
    `_RECONSIDERS_ON_BLOCK_VERSION` excepted: that build keeps the orphan,
    read off its own `getnetworkinfo` `version`
    ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
    """
    if not isinstance(node, BitcoindAdapter):
        return True
    version = node.rpc.call("getnetworkinfo")["version"]
    return bool(version >= _RECONSIDERS_ON_BLOCK_VERSION)


def parents_arriving_during_the_delay_are_not_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_arrival_timing_orphan`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 2)
    tx_parent_arrives = wallet.create_self_transfer()
    tx_parent_doesnt_arrive = wallet.create_self_transfer()
    # a fake orphan, spending outputs the two parents do not have
    tx_fake_orphan = wallet.create_self_transfer_multi(
        utxos_to_spend=[
            Utxo(OutPoint(parent.id, 10), _new_utxo(wallet, parent).value, 0, False)
            for parent in (tx_parent_doesnt_arrive, tx_parent_arrives)
        ]
    )
    with ExitStack() as stack:
        peer_spy = _inbound(stack, node)
        peer_normal = _inbound(stack, node)
        # the node asks for no parent at once
        peer_spy.assert_no_immediate_response(_tx(tx_fake_orphan))

        peer_normal.send_and_ping(_tx(tx_parent_arrives))
        assert tx_parent_arrives.id.hex() in _mempool(node)

        # the spy cannot ask for the parent it was not announced
        assert len(peer_spy.tx_invs) == 0
        peer_spy.assert_no_immediate_response(
            GetData([Inventory(InventoryType.MSG_WTX, tx_parent_arrives.hash)])
        )

        # neither parent is asked for within the non-preferred delay
        clock.bump(_NONPREF_PEER_TX_DELAY)
        peer_spy.assert_never_requested(tx_parent_arrives.id)
        peer_spy.assert_never_requested(tx_parent_doesnt_arrive.id)
        # the missing one is, once the txid delay has passed too
        clock.bump(_TXID_RELAY_DELAY)
        peer_spy.wait_for_parent_requests([tx_parent_doesnt_arrive.id])
        peer_spy.assert_never_requested(tx_parent_arrives.id)


def a_rejected_parent_is_requested_only_under_another_witness(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_rejected_parents_exceptions`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _fresh_node(cluster, skip_counts)
    coin_overly_large, coin_other = _p2pk_coins(node, 2)
    wallet, clock = _wallet(node, 2)
    with ExitStack() as stack:
        peer1 = _inbound(stack, node)
        peer2 = _inbound(stack, node)

        # a parent with no witness, refused for its size: its txid is its
        # wtxid, and so is known to be invalid
        parent_overly_large_nonsegwit = _p2pk_self_transfer(
            coin_overly_large, target_vsize=_OVERLY_LARGE_VSIZE
        )
        assert parent_overly_large_nonsegwit.id == parent_overly_large_nonsegwit.hash
        parent_other = _p2pk_self_transfer(coin_other)
        child_nonsegwit = _p2pk_self_transfer_multi(
            [
                _p2pk_new_utxo(parent_other),
                _p2pk_new_utxo(parent_overly_large_nonsegwit),
            ]
        )
        _relay_transaction(peer1, clock, parent_overly_large_nonsegwit)
        assert parent_overly_large_nonsegwit.id.hex() not in _mempool(node)

        # its child is refused, not kept, its parents asked of nobody
        _relay_transaction(peer2, clock, child_nonsegwit)
        assert child_nonsegwit.id.hex() not in _mempool(node)
        assert not in_orphanage(node, child_nonsegwit)
        clock.bump(_GETDATA_TX_INTERVAL)
        peer1.assert_never_requested(parent_other.id)
        peer2.assert_never_requested(parent_other.id)
        peer2.assert_never_requested(parent_overly_large_nonsegwit.id)

        # a parent refused for its fee, which its txid does not commit to
        parent_low_fee = wallet.create_self_transfer(fee_rate=0)
        child_low_fee = wallet.create_self_transfer(
            utxo_to_spend=_new_utxo(wallet, parent_low_fee)
        )
        _relay_transaction(peer1, clock, parent_low_fee)
        assert parent_low_fee.id.hex() not in _mempool(node)

        # its child is kept, and the parent asked for by txid
        _relay_transaction(peer2, clock, child_low_fee)
        assert child_low_fee.id.hex() not in _mempool(node)
        assert in_orphanage(node, child_low_fee)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer2.wait_for_getdata([parent_low_fee.id])

        # a parent refused with its witness stripped, which its txid does
        # not commit to either
        parent_normal = wallet.create_self_transfer()
        parent1_witness_stripped = Tx.parse(
            parent_normal.serialize(include_witness=False), check_validity=False
        )
        child_invalid_witness = wallet.create_self_transfer(
            utxo_to_spend=_new_utxo(wallet, parent_normal)
        )
        _relay_transaction(peer1, clock, parent1_witness_stripped)
        assert parent1_witness_stripped.id == parent_normal.id
        assert parent1_witness_stripped.id.hex() not in _mempool(node)

        # its child is kept, and the parent asked for by txid
        _relay_transaction(peer2, clock, child_invalid_witness)
        assert child_invalid_witness.id.hex() not in _mempool(node)
        assert in_orphanage(node, child_invalid_witness)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer2.wait_for_getdata([parent_normal.id])

        # the parent with its witness is taken in, and its child with it
        _relay_transaction(peer1, clock, parent_normal)
        assert set(_mempool(node)) == {
            parent_normal.id.hex(),
            child_invalid_witness.id.hex(),
        }


def parents_not_recently_confirmed_are_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_multiple_parents`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 4, Capability.INVALIDATE_BLOCK)
    with ExitStack() as stack:
        peer = _inbound(stack, node)

        # a parent confirmed long ago
        tx_conf_old = wallet.send_self_transfer()
        hashes = wallet.generate(10, confirm=[tx_conf_old])
        utxo_conf_old = wallet.get_utxo(txid=tx_conf_old.id.hex())

        # a block taken off the tip empties the node's filter of recently
        # confirmed transactions, which holds that parent until then
        node.rpc.call("invalidateblock", [hashes[-1].hex()])
        assert node.rpc.call("getbestblockhash") == hashes[-2].hex()
        _sync_validation_queue(node)
        wallet.resync()

        # a parent confirmed since
        tx_conf_recent = wallet.send_self_transfer()
        wallet.generate(1, confirm=[tx_conf_recent])
        _sync_validation_queue(node)
        utxo_conf_recent = wallet.get_utxo(txid=tx_conf_recent.id.hex())

        # a parent in the mempool, and one missing
        assert _mempool(node) == []
        mempool_tx = wallet.send_self_transfer()
        utxo_unconf_mempool = wallet.get_utxo(txid=mempool_tx.id.hex())
        missing_tx = wallet.create_self_transfer()
        assert missing_tx.id.hex() not in _mempool(node)

        orphan = wallet.create_self_transfer_multi(
            utxos_to_spend=[
                utxo_conf_old,
                utxo_conf_recent,
                utxo_unconf_mempool,
                _new_utxo(wallet, missing_tx),
            ]
        )

        # the orphan is kept, and the parents neither in the mempool nor
        # recently confirmed asked for
        _relay_transaction(peer, clock, orphan)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer.sync_with_ping()
        assert in_orphanage(node, orphan)
        assert len(peer.last_getdata) == 2
        peer.wait_for_parent_requests([tx_conf_old.id, missing_tx.id])

        # a `notfound` for the old parent does not drop the orphan, which is
        # taken in once the missing parent arrives
        peer.send(NotFound([Inventory(InventoryType.MSG_WITNESS_TX, tx_conf_old.id)]))
        peer.send_and_ping(_tx(missing_tx))
        assert _ancestor_count(node, orphan) == 3


def parents_already_requested_are_not_requested_again(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphans_overlapping_parents`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _fresh_node(cluster, skip_counts)
    confirmed_utxos = _p2pk_coins(node, 4)
    _, clock = _wallet(node, 0)
    # a parent of `child_a` alone, of both children, and of `child_b` alone
    missing_parent_a = _p2pk_self_transfer(confirmed_utxos[0])
    missing_parent_ab = _p2pk_self_transfer(confirmed_utxos[1])
    inflight_parent_ab = _p2pk_self_transfer(confirmed_utxos[2])
    missing_parent_b = _p2pk_self_transfer(confirmed_utxos[3])
    child_a = _p2pk_self_transfer_multi(
        [
            _p2pk_new_utxo(missing_parent_a),
            _p2pk_new_utxo(missing_parent_ab),
            _p2pk_new_utxo(inflight_parent_ab),
        ]
    )
    child_b = _p2pk_self_transfer_multi(
        [
            _p2pk_new_utxo(missing_parent_b),
            _p2pk_new_utxo(missing_parent_ab),
            _p2pk_new_utxo(inflight_parent_ab),
        ]
    )
    # the missing input and the request in flight name one transaction only
    # where its txid is its wtxid
    assert inflight_parent_ab.id == inflight_parent_ab.hash
    with ExitStack() as stack:
        peer_txrequest = _inbound(stack, node)
        peer_orphans = _inbound(stack, node)

        # `inflight_parent_ab` is announced and asked for
        peer_txrequest.send_and_ping(
            _inv(InventoryType.MSG_WTX, inflight_parent_ab.hash)
        )
        clock.bump(_NONPREF_PEER_TX_DELAY)
        peer_txrequest.wait_for_getdata([inflight_parent_ab.hash])

        # a parent whose request is in flight is not asked for again
        _relay_transaction(peer_orphans, clock, child_a)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        assert in_orphanage(node, child_a)
        peer_orphans.wait_for_parent_requests(
            [missing_parent_a.id, missing_parent_ab.id]
        )

        # nor is one whose request for another orphan is in flight
        _relay_transaction(peer_orphans, clock, child_b)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        assert in_orphanage(node, child_b)
        peer_orphans.wait_for_parent_requests([missing_parent_b.id])
        peer_orphans.assert_never_requested(inflight_parent_ab.id)

        # until the first request expires unanswered
        clock.bump(_GETDATA_TX_INTERVAL)
        peer_orphans.wait_for_parent_requests([inflight_parent_ab.id])


def a_parent_kept_as_an_orphan_is_not_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_of_orphan`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _fresh_node(cluster, skip_counts)
    coin_grandparent, coin_parent = _p2pk_coins(node, 2)
    _, clock = _wallet(node, 0)
    missing_grandparent = _p2pk_self_transfer(coin_grandparent)
    missing_parent_orphan = _p2pk_self_transfer(_p2pk_new_utxo(missing_grandparent))
    missing_parent = _p2pk_self_transfer(coin_parent)
    orphan = _p2pk_self_transfer_multi(
        [_p2pk_new_utxo(missing_parent), _p2pk_new_utxo(missing_parent_orphan)]
    )
    with ExitStack() as stack:
        peer = _inbound(stack, node)

        # a parent is kept as an orphan, and its own parent asked for
        _relay_transaction(peer, clock, missing_parent_orphan)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        assert in_orphanage(node, missing_parent_orphan)
        peer.wait_for_parent_requests([missing_grandparent.id])

        # its child is kept, and asked only for the parent the node lacks
        _relay_transaction(peer, clock, orphan)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        assert in_orphanage(node, orphan)
        peer.wait_for_parent_requests([missing_parent.id])


def an_orphan_is_reconsidered_once_its_parent_is_mined(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_parent_confirmed`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1)
    parent = wallet.create_self_transfer(fee_rate=0)
    child = wallet.create_self_transfer(utxo_to_spend=_new_utxo(wallet, parent))
    with ExitStack() as stack:
        peer = _inbound(stack, node)
        _relay_transaction(peer, clock, child)
        assert in_orphanage(node, child)

        # the parent is asked for and withheld, reaching the node in a block
        clock.bump(_TXREQUEST_TIME_SKIP)
        peer.wait_for_parent_requests([parent.id])
        assert _mempool(node) == []

        wallet.generate(1, confirm=[parent])
        if _reconsiders_on_block(node):
            wait_until(lambda: child.id.hex() in _mempool(node), timeout=_WAIT)
            assert not in_orphanage(node, child)
        else:
            peer.sync_with_ping()
            assert child.id.hex() not in _mempool(node)
            assert in_orphanage(node, child)


def descendants_of_a_rejected_parent_are_rejected_too(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_inherit_rejection`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node = _fresh_node(cluster, skip_counts)
    (coin,) = _p2pk_coins(node, 1)
    wallet, clock = _wallet(node, 0)
    # a parent with no witness, refused for its size, and two descendants
    # that have one
    parent_overly_large_nonsegwit = _p2pk_self_transfer(
        coin, target_vsize=_OVERLY_LARGE_VSIZE
    )
    assert parent_overly_large_nonsegwit.id == parent_overly_large_nonsegwit.hash
    child = wallet.create_self_transfer(
        utxo_to_spend=_p2pk_new_utxo(parent_overly_large_nonsegwit)
    )
    grandchild = wallet.create_self_transfer(utxo_to_spend=_new_utxo(wallet, child))
    assert child.id != child.hash
    assert grandchild.id != grandchild.hash
    with ExitStack() as stack:
        peer1 = _inbound(stack, node)
        peer2 = _inbound(stack, node)
        # announcing by txid
        peer3 = _inbound(stack, node, wtxidrelay=False)

        _relay_transaction(peer1, clock, parent_overly_large_nonsegwit)
        assert parent_overly_large_nonsegwit.id.hex() not in _mempool(node)

        # the child is refused, not kept, and its parent not asked for
        # again once an orphan's would be
        _relay_transaction(peer1, clock, child)
        assert len(_mempool(node)) == 0
        assert not in_orphanage(node, child)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer1.sync_with_ping()
        assert [item.hash for item in peer1.last_getdata] == [child.hash]

        # the grandchild is refused too, its parent asked for by neither hash
        _relay_transaction(peer2, clock, grandchild)
        assert len(_mempool(node)) == 0
        assert not in_orphanage(node, grandchild)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer2.assert_never_requested(child.id)
        peer2.assert_never_requested(child.hash)

        # the child is not asked for by txid, whatever witness it might carry
        peer3.send_and_ping(_inv(InventoryType.MSG_TX, child.id))
        clock.bump(_TXREQUEST_TIME_SKIP)
        peer3.assert_never_requested(child.id)


def an_orphan_of_the_same_txid_is_kept_too(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_same_txid_orphan`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1, Capability.DEBUG_LOG)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    tx_parent = wallet.create_self_transfer()
    tx_child = wallet.create_self_transfer(utxo_to_spend=_new_utxo(wallet, tx_parent))
    tx_orphan_bad_wit = malleated_to_invalid_witness(tx_child)
    with ExitStack() as stack:
        bad_peer = _inbound(stack, node)
        honest_peer = _inbound(stack, node)

        # the fake orphan arrives first, its parent missing
        bad_peer.send_and_ping(_tx(tx_orphan_bad_wit))
        assert in_orphanage(node, tx_orphan_bad_wit)

        # the parent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        bad_peer.wait_for_getdata([tx_parent.id])

        # the real child, missing the same parent, is kept too
        with assert_debug_log(node.debug_log_path, ["missingorspent"], timeout=0):
            honest_peer.send_and_ping(_tx(tx_child))
        assert in_orphanage(node, tx_child)

        # the request to the bad peer expires, and the honest one is asked
        clock.bump(_GETDATA_TX_INTERVAL)
        honest_peer.wait_for_getdata([tx_parent.id])
        honest_peer.send_and_ping(_tx(tx_parent))

        # the real child is taken in and the fake one refused
        node_mempool = _mempool(node)
        assert tx_parent.id.hex() in node_mempool
        assert tx_child.id.hex() in node_mempool
        assert _mempool_wtxid(node, tx_child) == tx_child.hash.hex()


def a_parent_of_the_same_txid_is_requested_again(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_same_txid_orphan_of_orphan`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1)
    tx_grandparent = wallet.create_self_transfer()
    # both a parent and a child, kept in the orphanage
    tx_middle = wallet.create_self_transfer(
        utxo_to_spend=_new_utxo(wallet, tx_grandparent)
    )
    tx_orphan_bad_wit = malleated_to_invalid_witness(tx_middle)
    # spending `tx_middle`, and so `tx_orphan_bad_wit`, of the same txid
    tx_grandchild = wallet.create_self_transfer(
        utxo_to_spend=_new_utxo(wallet, tx_middle)
    )
    with ExitStack() as stack:
        bad_peer = _inbound(stack, node)
        honest_peer = _inbound(stack, node)

        # the fake orphan arrives first, its parent missing
        bad_peer.send_and_ping(_tx(tx_orphan_bad_wit))
        assert in_orphanage(node, tx_orphan_bad_wit)

        # the grandparent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        bad_peer.wait_for_getdata([tx_grandparent.id])

        # the grandchild's parent is kept by its txid, and asked for again,
        # a witness the node does not assume
        honest_peer.send_and_ping(_tx(tx_grandchild))
        assert in_orphanage(node, tx_grandchild)
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        honest_peer.wait_for_getdata([tx_middle.id])

        # the real middle, its own parent missing, is kept too
        honest_peer.send_and_ping(_tx(tx_middle))
        assert in_orphanage(node, tx_middle)
        assert len(_mempool(node)) == 0

        honest_peer.send_and_ping(_tx(tx_grandparent))

        # the real middle and the grandchild are taken in, the fake refused
        node_mempool = _mempool(node)
        assert tx_grandparent.id.hex() in node_mempool
        assert tx_middle.id.hex() in node_mempool
        assert tx_grandchild.id.hex() in node_mempool
        assert _mempool_wtxid(node, tx_middle) == tx_middle.hash.hex()
        wait_until(lambda: node.rpc.call("getorphantxs") == [], timeout=_WAIT)


def an_inv_by_an_orphan_txid_is_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_txid_inv`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1)
    tx_parent = wallet.create_self_transfer()
    tx_child = wallet.create_self_transfer(utxo_to_spend=_new_utxo(wallet, tx_parent))
    tx_orphan_bad_wit = malleated_to_invalid_witness(tx_child)
    with ExitStack() as stack:
        bad_peer = _inbound(stack, node)
        # announcing by txid, which a wtxid peer's `inv` would not be
        honest_peer = _inbound(stack, node, wtxidrelay=False)

        # the fake orphan arrives first, its parent missing
        bad_peer.send_and_ping(_tx(tx_orphan_bad_wit))
        assert in_orphanage(node, tx_orphan_bad_wit)

        # the parent is asked for by txid
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        bad_peer.wait_for_getdata([tx_parent.id])

        # the real child, announced by txid, is asked for and kept
        honest_peer.send_and_ping(_inv(InventoryType.MSG_TX, tx_child.id))
        clock.bump(_TXREQUEST_TIME_SKIP)
        honest_peer.wait_for_getdata([tx_child.id])
        honest_peer.send_and_ping(_tx(tx_child))
        assert in_orphanage(node, tx_child)

        # the first request for the parent expires, and it is asked again
        clock.bump(_GETDATA_TX_INTERVAL)
        honest_peer.wait_for_getdata([tx_parent.id])
        honest_peer.send_and_ping(_tx(tx_parent))

        # the real child is taken in and the fake one refused, in either order
        node_mempool = _mempool(node)
        assert tx_parent.id.hex() in node_mempool
        assert tx_child.id.hex() in node_mempool
        assert _mempool_wtxid(node, tx_child) == tx_child.hash.hex()
        wait_until(lambda: node.rpc.call("getorphantxs") == [], timeout=_WAIT)


def an_outbound_announcer_is_asked_for_parents_first(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_orphan_handling_prefer_outbound`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1, Capability.TYPED_OUTBOUND)
    parent_tx, orphan_tx = _parent_and_child(wallet)
    orphan_inv = _inv(InventoryType.MSG_WTX, orphan_tx.hash)
    with ExitStack() as stack:
        peer_inbound = _inbound(stack, node)
        peer_outbound = _outbound(stack, node)

        # the inbound peer relays the orphan
        peer_inbound.send_and_ping(orphan_inv)
        clock.bump(_TXREQUEST_TIME_SKIP)
        peer_inbound.wait_for_getdata([orphan_tx.hash])

        # both announce it, so either is expected to know its parents
        peer_outbound.send_and_ping(orphan_inv)
        peer_inbound.send_and_ping(_tx(orphan_tx))

        orphanage = _orphans(node)
        assert orphanage[0]["wtxid"] == orphan_tx.hash.hex()
        assert _announcers(node) == 2

        # the outbound peer is asked for the parent, and the inbound one not
        clock.bump(_TXID_RELAY_DELAY)
        peer_outbound.wait_for_parent_requests([parent_tx.id])
        peer_inbound.assert_never_requested(parent_tx.id)

        # the inbound peer is asked once the first request expires
        clock.bump(_GETDATA_TX_INTERVAL)
        peer_inbound.sync_with_ping()
        peer_inbound.wait_for_parent_requests([parent_tx.id])


def every_announcer_is_asked_for_parents(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_announcers_before_and_after`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1, Capability.TYPED_OUTBOUND)
    parent_tx, orphan_tx = _parent_and_child(wallet)
    orphan_inv = _inv(InventoryType.MSG_WTX, orphan_tx.hash)
    with ExitStack() as stack:
        # announcing ahead of the orphan, one disconnecting while asked for
        # its parent and one never answering
        peer_early_disconnected = _outbound(stack, node)
        peer_early_unresponsive = _inbound(stack, node)
        # announcing after it
        peer_late_announcer = _inbound(stack, node)

        peer_early_disconnected.send_and_ping(orphan_inv)
        clock.bump(_TXREQUEST_TIME_SKIP)
        peer_early_disconnected.wait_for_getdata([orphan_tx.hash])
        peer_early_unresponsive.send_and_ping(orphan_inv)
        peer_early_disconnected.send_and_ping(_tx(orphan_tx))

        # one orphan, announced by both
        orphanage = _orphans(node)
        assert len(orphanage) == 1
        assert orphanage[0]["wtxid"] == orphan_tx.hash.hex()
        assert _announcers(node) == 2

        # the peer asked for the parent disconnects, leaving one announcer
        clock.bump(_TXID_RELAY_DELAY)
        peer_early_disconnected.wait_for_parent_requests([parent_tx.id])
        peer_early_disconnected.peer.close()
        wait_until(lambda: _announcers(node) == 1, timeout=_WAIT)

        # the other early announcer is asked, an inbound peer's delay later
        clock.bump(_NONPREF_PEER_TX_DELAY)
        peer_early_unresponsive.wait_for_parent_requests([parent_tx.id])

        # a peer announcing the orphan now is an announcer too
        peer_late_announcer.send_and_ping(orphan_inv)
        orphanage = _orphans(node)
        assert orphanage[0]["wtxid"] == orphan_tx.hash.hex()
        assert _announcers(node) == 2

        clock.bump(_GETDATA_TX_INTERVAL)
        peer_late_announcer.wait_for_parent_requests([parent_tx.id])


def a_parent_gone_missing_is_requested(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_parents_change`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 4)
    # an orphan of two parents: one missing, one in the mempool on arrival
    parent_missing = wallet.create_self_transfer()

    # `parent_peekaboo_ab` spends coins A and B; `tx_replacer_bc` replaces
    # it over B, and `tx_replacer_c` replaces that over C, so that
    # `parent_peekaboo_ab` can come back with no package replacement
    coin_a = wallet.get_utxo(confirmed_only=True)
    coin_b = wallet.get_utxo(confirmed_only=True)
    coin_c = wallet.get_utxo(confirmed_only=True)
    parent_peekaboo_ab = wallet.create_self_transfer_multi(
        utxos_to_spend=[coin_a, coin_b], fee_per_output=_FEE_INCREMENT
    )
    tx_replacer_bc = wallet.create_self_transfer_multi(
        utxos_to_spend=[coin_b, coin_c], fee_per_output=2 * _FEE_INCREMENT
    )
    tx_replacer_c = wallet.create_self_transfer(utxo_to_spend=coin_c)

    _send_raw(node, parent_peekaboo_ab)

    orphan = wallet.create_self_transfer_multi(
        utxos_to_spend=[
            _new_utxo(wallet, parent_peekaboo_ab),
            _new_utxo(wallet, parent_missing),
        ]
    )
    orphan_inv = _inv(InventoryType.MSG_WTX, orphan.hash)
    with ExitStack() as stack:
        # peer1 sends the orphan and is asked for the missing parent
        peer1 = _inbound(stack, node)
        peer1.send_and_ping(orphan_inv)
        clock.bump(_TXREQUEST_TIME_SKIP)
        peer1.wait_for_getdata([orphan.hash])
        peer1.send_and_ping(_tx(orphan))
        wait_until(
            lambda: (
                node.rpc.call("getorphantxs", {"verbosity": 0}) == [orphan.id.hex()]
            ),
            timeout=_WAIT,
        )
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer1.wait_for_getdata([parent_missing.id])

        # the parent in the mempool is replaced, and so goes missing, and
        # its replacement is replaced, so that it can be sent again
        _send_raw(node, tx_replacer_bc)
        assert tx_replacer_bc.id.hex() in _mempool(node)
        _send_raw(node, tx_replacer_c)
        node_mempool = _mempool(node)
        assert tx_replacer_bc.id.hex() not in node_mempool
        assert parent_peekaboo_ab.id.hex() not in node_mempool
        assert tx_replacer_c.id.hex() in node_mempool

        # peer2 announces the orphan too, its missing parents now different
        peer2 = _inbound(stack, node)
        peer2.send_and_ping(orphan_inv)
        assert _announcers(node) == 2

        # peer1 disconnects, and peer2 is asked for both parents
        peer1.peer.close()
        wait_until(lambda: len(node.rpc.call("getpeerinfo")) == 1, timeout=_WAIT)
        peer2.sync_with_ping()
        clock.bump(_TXREQUEST_TIME_SKIP)
        wait_until(lambda: _announcers(node) == 1, timeout=_WAIT)
        peer2.wait_for_parent_requests([parent_peekaboo_ab.id, parent_missing.id])
        peer2.send_and_ping(_tx(parent_missing))
        peer2.send_and_ping(_tx(parent_peekaboo_ab))

        final_mempool = _mempool(node)
        assert parent_missing.id.hex() in final_mempool
        assert parent_peekaboo_ab.id.hex() in final_mempool
        assert orphan.id.hex() in final_mempool
        assert tx_replacer_c.id.hex() in final_mempool


def a_maximal_ancestor_package_is_protected_in_the_orphanage(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_maximal_package_protected`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet, clock = _node(cluster, skip_counts, 1)
    large_orphans = [_large_orphan() for _ in range(_LARGE_ORPHANS)]

    # each is an orphan, and within the standard size an orphan is kept at
    for large_orphan in large_orphans:
        (result,) = node.rpc.call(
            "testmempoolaccept", [[large_orphan.serialize(True).hex()]]
        )
        assert not result["allowed"]
        assert result["reject-reason"] == "missing-inputs"

    with ExitStack() as stack:
        peer_normal = _inbound(stack, node)
        peer_doser = _inbound(stack, node)

        # a large orphan from each of a set of peers, its parent asked for
        for large_orphan in large_orphans[:_INDIVIDUAL_DOSERS]:
            peer_doser_individual = _inbound(stack, node)
            peer_doser_individual.send_and_ping(_tx(large_orphan))
            clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY + 1)
            peer_doser_individual.wait_for_getdata([large_orphan.vin[0].prev_out.tx_id])
        wait_until(
            lambda: len(node.rpc.call("getorphantxs")) == _INDIVIDUAL_DOSERS,
            timeout=_WAIT,
        )

        # an ancestor package of the largest size, off one missing parent
        ancestor_package = wallet.create_self_transfer_chain(
            chain_length=_DEFAULT_ANCESTOR_LIMIT - 1
        )
        final_tx = wallet.create_self_transfer(
            utxo_to_spend=_new_utxo(wallet, ancestor_package[-1]),
            target_vsize=_MAXIMAL_PACKAGE_VSIZE
            - sum(tx.vsize for tx in ancestor_package),
        )
        ancestor_package.append(final_tx)

        # every transaction but that parent is kept as an orphan
        for orphan in ancestor_package[1:]:
            peer_normal.send_and_ping(_tx(orphan))
        orphan_set = node.rpc.call("getorphantxs")
        for orphan in ancestor_package[1:]:
            assert orphan.id.hex() in orphan_set

        # and the parent asked for
        clock.bump(_NONPREF_PEER_TX_DELAY + _TXID_RELAY_DELAY)
        peer_normal.wait_for_request(ancestor_package[0].id)

        # the rest of the large orphans, from one peer
        for large_orphan in large_orphans[_INDIVIDUAL_DOSERS:]:
            peer_doser.send_and_ping(_tx(large_orphan))

        # the parent arrives, and the whole package is taken in
        peer_normal.send_and_ping(_tx(ancestor_package[0]))
        wait_until(
            lambda: _ancestor_count(node, final_tx) == _DEFAULT_ANCESTOR_LIMIT,
            timeout=_WAIT,
        )
