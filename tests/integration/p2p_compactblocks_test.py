# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks`, a first batch, as bodies over either node.

Read from Core's `test/functional/p2p_compactblocks.py` (`28641fd195db`,
2026-07-31): how a node negotiates, builds, serves and takes BIP152's
compact blocks. Each of the checks below is one of Core's `test_*`
methods, a body over a fresh node:

- a node announces new blocks as `cmpctblock` only to a peer whose
  `sendcmpct` asks for it at version 2, and stops once one asks it not
  to;
- a `cmpctblock` a node announces, or sends for a `getdata`, prefills
  its coinbase and carries every other transaction as the short id
  BIP152 derives from its wtxid;
- a block announced by `inv` or by `headers` is asked for as a compact
  one, and a `blocktxn` carrying what the node asks for completes it;
- a node asks only for the transactions of a `cmpctblock` it has not
  got, and asks for none once its mempool holds them all;
- a node answers a `getblocktxn` for a block near its tip with those
  transactions and one for a deeper block with the whole block, and
  drops a peer asking for an index past the block;
- a block deeper than Core's `MAX_CMPCTBLOCK_DEPTH` is sent whole where
  a compact one is asked for, and a `cmpctblock` for a block off the
  tip leaves only its header;
- a `blocktxn` that does not complete the block has the node ask for
  the whole of it;
- a block submitted over RPC is announced as `cmpctblock` to every peer
  asking for it.

Every body mines its coins first (`Capability.MINE`,
`mini_wallet.MiniWallet`), which also leaves initial block download,
where a node neither asks for compact blocks nor announces them. BIP152's
messages are btclib's own `btclib.p2p.compact_blocks`, and `_cmpctblock`
below builds one the way Core's `HeaderAndShortIDs.initialize_from_block`
does at `use_witness=True`.

Core's `TestP2PConn` records what the node sends from its framework's
network thread. Here `_Conn` does so on the test's own thread, where a
wait reads the peer's connection: a wait reads the peer up to the `pong`
of a ping round trip ahead of every poll, and a check that the node sent
nothing reads it up to that `pong` once.

What differs from Core's file besides:

- Core runs every check over one node and its peers, each check starting
  from the chain and the peer state the checks before it left; here each
  body starts a fresh node and builds that state itself. A body sending
  a `cmpctblock` the node did not ask for first has its peer send a
  `sendcmpct` and deliver a block, which makes it a high-bandwidth peer,
  as Core's earlier checks have made it: a node carrying
  bitcoin/bitcoin#32606 ignores such a `cmpctblock` from any other peer;
- Core fills its blocks with transactions paying and spending bare
  `OP_TRUE` scripts, which its node takes into the mempool only under the
  `-acceptnonstdtxn=1` it starts with; here `MiniWallet`'s own
  transactions fill them, and the node starts with no option;
- Core runs `test_sendcmpct` over each of its peers, an outbound one
  among them; here it runs over an inbound peer;
- Core's `test_getblocktxn_handler` reads the blocks its earlier checks
  left; here each block it reads carries a chain of transactions;
- the log line Core's `test_getblocktxn_handler` reads beside the
  disconnect for an index past the block is not asserted.

Core's other checks are not ported yet. Those about a malformed or
invalid message, and whether the node drops the peer that sent it,
several reading the node's log beside it:
`test_invalid_sendcmpct_announce`, `test_invalid_cmpctblock_message`,
`test_multiple_blocktxn_response`, `test_invalid_tx_in_compactblock`,
`test_empty_getblocktxn_disconnects` and `test_low_work_compactblocks`.
And those about which peers a node selects for high-bandwidth mode and
takes a `cmpctblock` from: `test_compactblock_reconstruction_stalling_peer`,
`test_compactblock_reconstruction_parallel_reconstruction`, whose
outbound peer asks for `Capability.TYPED_OUTBOUND`,
`test_highbandwidth_mode_states_via_getpeerinfo` and
`test_compact_blocks_ignored`. Of these, `test_invalid_sendcmpct_announce`,
`test_empty_getblocktxn_disconnects` and `test_compact_blocks_ignored`
check what the pinned release does not do.

`p2p_compactblocks_bitcoind_test.py` and
`p2p_compactblocks_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import random
import secrets
import time
from contextlib import ExitStack
from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.block.mining import mine
from btclib.p2p import (
    BlockPayload,
    BlockTxn,
    CmpctBlock,
    GetBlockTxn,
    GetData,
    GetHeaders,
    Headers,
    Inv,
    Inventory,
    InventoryType,
    Ping,
    Pong,
    PrefilledTransaction,
    SendCmpct,
    SendHeaders,
    TxPayload,
)
from btclib.p2p.magic import magic_from_chain
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, build_next_block
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message, Payload
    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.mini_wallet import Utxo
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_block_off_the_tip_is_not_sent_compact",
    "a_compact_block_is_built_as_bip152_says",
    "a_submitted_block_is_announced_compact",
    "a_wrong_blocktxn_falls_back_to_the_block",
    "an_announced_block_is_asked_for_compact",
    "getblocktxn_is_answered_near_the_tip",
    "only_missing_transactions_are_asked_for",
    "sendcmpct_negotiates_compact_announcements",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# Core's own default wait, `P2PInterface`'s and `wait_until`'s, and the
# one most of its waits here pass
_WAIT = 60.0
_SHORT_WAIT = 30.0

# Core's own constants (`p2p_compactblocks.py`)
_MAX_GETBLOCKTXN_DEPTH = 10
_MAX_CMPCTBLOCK_DEPTH = 5

# Core's own count of transactions `test_compactblock_construction` sends
_CONSTRUCTION_TRANSACTIONS = 25

# the transactions each block `getblocktxn_is_answered_near_the_tip`
# reads carries, beside its coinbase
_HANDLER_CHAIN_LENGTH = 3

# Core's own `CMPCTBLOCKS_VERSION`, and the versions on either side of it
_VERSION = 2


class _Conn:
    """Core's own `TestP2PConn`: a peer recording the blocks announced to it.

    `Peer.wait_for` drops what it does not wait for, so every wait here
    reads the connection itself and hands each message to `_handle`
    first. `announced` is the hash of every block a `cmpctblock`, a
    `headers` or an `inv` named, Core's `announced_blockhashes`, and
    `block_announced` whether one has since `clear_block_announcement`.
    What the node sent last of each command is `Peer.last_message`,
    Core's `last_message`.

    :param peer: the connection, its handshake done.
    """

    def __init__(self, peer: Peer) -> None:
        self.peer = peer
        self.announced: set[bytes] = set()
        self.block_announced = False

    def send(self, payload: Payload) -> None:
        """Core's own `send_without_ping`."""
        self.peer.send(payload, check_validity=False)

    def _handle(self, message: Message) -> None:
        """Core's `on_cmpctblock`, `on_headers`, `on_inv`, and `on_ping`."""
        if message.command == "ping":
            self.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "cmpctblock":
            self.block_announced = True
            self.announced.add(_parse_cmpctblock(message).header.hash)
        elif message.command == "headers":
            self.block_announced = True
            headers = Headers.parse(message.payload, check_validity=False).headers
            self.announced.update(header.hash for header in headers)
        elif message.command == "inv":
            for item in Inv.parse(message.payload).items:
                if item.type_code == InventoryType.MSG_BLOCK:
                    self.block_announced = True
                    self.announced.add(item.hash)

    def sync_with_ping(self) -> None:
        """`Peer.sync_with_ping`'s barrier, every message read handled.

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

    def wait_until(
        self, predicate: Callable[[], bool], *, timeout: float = _SHORT_WAIT
    ) -> None:
        """Core's own `P2PInterface.wait_until`, the peer read before a poll."""

        def _served() -> bool:
            self.sync_with_ping()
            return predicate()

        wait_until(_served, timeout=timeout)

    def has(self, command: str) -> bool:
        """Whether the node has sent a `command` since it was last cleared."""
        return command in self.peer.last_message

    def last(self, command: str) -> Message:
        """Core's own `last_message[command]`."""
        return self.peer.last_message[command]

    def clear(self, *commands: str) -> None:
        """Forget the last message of each of `commands`."""
        for command in commands:
            self.peer.last_message.pop(command, None)

    def clear_block_announcement(self) -> None:
        """Core's own `clear_block_announcement`."""
        self.block_announced = False
        self.clear("inv", "headers", "cmpctblock")

    def request_headers_and_sync(self, tip: bytes) -> None:
        """Core's own `request_headers_and_sync(locator=[tip])`."""
        self.clear_block_announcement()
        self.send(GetHeaders(locator=[tip]))
        self.wait_until(lambda: self.block_announced)
        self.clear_block_announcement()

    def wait_for_block_announcement(self, block_hash: bytes) -> None:
        """Core's own `wait_for_block_announcement`."""
        self.wait_until(lambda: block_hash in self.announced)

    def wait_for_getdata(self, block_hash: bytes) -> None:
        """Core's own `wait_for_getdata([block_hash])`: the latest names it."""

        def _asked() -> bool:
            if not self.has("getdata"):
                return False
            items = GetData.parse(self.last("getdata").payload).items
            return [item.hash for item in items] == [block_hash]

        self.wait_until(_asked)


def _parse_cmpctblock(message: Message) -> CmpctBlock:
    return CmpctBlock.parse(message.payload, check_validity=False)


def _cmpctblock(block: Block, prefill: Sequence[int] = (0,)) -> CmpctBlock:
    """Core's `HeaderAndShortIDs.initialize_from_block`, `use_witness=True`.

    The transactions at `prefill` are sent whole, and every other one as
    the short id of its wtxid, under the nonce Core's own leaves at zero.
    """
    keyed = CmpctBlock(block.header, check_validity=False)
    return CmpctBlock(
        block.header,
        keyed.nonce,
        [
            keyed.short_id(tx.hash)
            for index, tx in enumerate(block.transactions)
            if index not in prefill
        ],
        [
            PrefilledTransaction(index, block.transactions[index], check_validity=False)
            for index in prefill
        ],
        check_validity=False,
    )


def _tx(tx: Tx) -> TxPayload:
    """Core's own `msg_tx(tx)`, its witness serialized."""
    return TxPayload(tx, include_witness=True, check_validity=False)


def _block_payload(block: Block) -> BlockPayload:
    """Core's own `msg_block(block)`, witnesses included."""
    return BlockPayload(block, include_witness=True, check_validity=False)


def _tip(node: NodeAdapter) -> bytes:
    """Return the node's own `getbestblockhash`, in display order."""
    return bytes.fromhex(node.rpc.call("getbestblockhash"))


def _mempool(node: NodeAdapter) -> list[str]:
    """Return the node's own `getrawmempool`."""
    txids = node.rpc.call("getrawmempool")
    assert isinstance(txids, list)
    return txids


def _read_block(node: NodeAdapter, block_hash: bytes) -> Block:
    """Return the node's own block at `block_hash`, read over `getblock`."""
    block_hex = node.rpc.call("getblock", [block_hash.hex(), 0])
    # the header's own check defaults to mainnet's proof-of-work limit
    return Block.parse(bytes.fromhex(block_hex), check_validity=False)


def _node(
    cluster: _Cluster, skip_counts: SkipCounts, coins: int
) -> tuple[NodeAdapter, MiniWallet]:
    """Return a fresh node out of initial block download, and its wallet.

    :param coins: the matured coins the body spends.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + coins)
    return node, wallet


def _connect(stack: ExitStack, node: NodeAdapter) -> _Conn:
    """Core's own `add_p2p_connection(TestP2PConn())`."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake()
    conn = _Conn(peer)
    conn.sync_with_ping()
    return conn


def _chain_block(
    node: NodeAdapter, wallet: MiniWallet, utxo: Utxo, count: int
) -> tuple[Block, Utxo]:
    """Core's own `build_block_with_transactions`, and the coin it leaves.

    A block on the node's tip carrying a chain of `count` transactions
    from `utxo`, each spending the one before it, unsubmitted; the coin
    is the last transaction's own, Core's `self.utxos.append`.
    """
    chain = wallet.create_self_transfer_chain(chain_length=count, utxo_to_spend=utxo)
    block = build_next_block(node, wallet.script_pub_key, chain)
    return block, wallet.new_utxos(chain[-1])[0]


def _request_cb_announcements(conn: _Conn, node: NodeAdapter) -> None:
    """Core's own `request_cb_announcements`.

    The `getheaders` for the tip is what has the node count the peer as
    holding the tip's header, which is what it announces a child of as a
    `cmpctblock` on.
    """
    conn.send(GetHeaders(locator=[_tip(node)]))
    conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))


def _make_high_bandwidth(conn: _Conn, node: NodeAdapter, wallet: MiniWallet) -> None:
    """Core's own `make_peer_hb_to_candidate`, the node's selection asserted.

    The peer delivers a block on the tip, which has a node that the peer
    has sent a `sendcmpct` select it for high-bandwidth mode, the node's
    own `sendcmpct` asking it to announce new blocks as `cmpctblock`.
    The wallet is resynced to the tip the block moves.
    """
    block = build_next_block(node, wallet.script_pub_key)
    conn.send_and_ping(_block_payload(block))
    assert _tip(node) == block.header.hash
    assert SendCmpct.parse(conn.last("sendcmpct").payload).announce is True
    wallet.resync()


def _getblocktxn_expected(
    conn: _Conn, block_hash: bytes, indexes: Sequence[int] | None = None
) -> None:
    """Core's own `getblocktxn_expected`: the node asked for `indexes`."""
    assert conn.has("getblocktxn")
    request = GetBlockTxn.parse(conn.last("getblocktxn").payload)
    assert request.block_hash == block_hash
    if indexes is not None:
        assert list(request.indexes) == list(indexes)


def sendcmpct_negotiates_compact_announcements(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_sendcmpct`, over one inbound peer.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 0)
    with ExitStack() as stack:
        conn = _connect(stack, node)

        # the node's own sendcmpct offers version 2
        conn.wait_until(lambda: conn.has("sendcmpct"))
        assert SendCmpct.parse(conn.last("sendcmpct").payload).version == _VERSION

        tip = _tip(node)

        def check_announcement_of_new_block(predicate: Callable[[], bool]) -> None:
            conn.clear_block_announcement()
            (block_hash,) = wallet.generate(1)
            conn.wait_for_block_announcement(block_hash)
            assert conn.block_announced
            assert predicate()

        def no_cmpctblock() -> bool:
            return not conn.has("cmpctblock")

        # no block is announced as a cmpctblock yet
        check_announcement_of_new_block(no_cmpctblock)

        # nor after the peer asks for headers
        conn.request_headers_and_sync(tip)
        check_announcement_of_new_block(lambda: no_cmpctblock() and conn.has("inv"))

        # a sendcmpct asking at a version below or above 2 is ignored
        conn.request_headers_and_sync(tip)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION - 1))
        check_announcement_of_new_block(no_cmpctblock)

        conn.request_headers_and_sync(tip)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION + 1))
        check_announcement_of_new_block(no_cmpctblock)

        # as is one at version 2 not asking to be announced to
        conn.request_headers_and_sync(tip)
        conn.send_and_ping(SendCmpct(announce=False, version=_VERSION))
        check_announcement_of_new_block(no_cmpctblock)

        # one at version 2 asking to be is announced to, block after block
        conn.request_headers_and_sync(tip)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))
        check_announcement_of_new_block(lambda: conn.has("cmpctblock"))
        check_announcement_of_new_block(lambda: conn.has("cmpctblock"))

        # after a sendheaders too
        conn.send_and_ping(SendHeaders())
        check_announcement_of_new_block(lambda: conn.has("cmpctblock"))

        # and after a version 1 sendcmpct not asking to be
        conn.send_and_ping(SendCmpct(announce=False, version=_VERSION - 1))
        check_announcement_of_new_block(lambda: conn.has("cmpctblock"))

        # until a version 2 one asks not to be, headers announcing instead
        conn.send_and_ping(SendCmpct(announce=False, version=_VERSION))
        check_announcement_of_new_block(lambda: no_cmpctblock() and conn.has("headers"))


def _check_compactblock_construction(
    cmpct: CmpctBlock, block_hash: bytes, block: Block
) -> None:
    """Core's own `check_compactblock_construction_from_block`."""
    assert cmpct.header.hash == block_hash

    # the coinbase is prefilled, and each prefilled transaction is the
    # block's own, its witness included
    assert len(cmpct.prefilled_txns) >= 1
    assert cmpct.prefilled_txns[0].index == 0
    for entry in cmpct.prefilled_txns:
        assert entry.tx.id == block.transactions[entry.index].id
        assert entry.tx.hash == block.transactions[entry.index].hash

    # every transaction is announced, and every short id is BIP152's
    assert cmpct.tx_count == len(block.transactions)
    prefilled = {entry.index for entry in cmpct.prefilled_txns}
    short_ids = iter(cmpct.short_ids)
    for index, tx in enumerate(block.transactions):
        if index not in prefilled:
            assert next(short_ids) == cmpct.short_id(tx.hash)


def a_compact_block_is_built_as_bip152_says(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_compactblock_construction`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, _CONSTRUCTION_TRANSACTIONS)
    with ExitStack() as stack:
        conn = _connect(stack, node)
        wallet.generate(1)

        txs = [wallet.send_self_transfer() for _ in range(_CONSTRUCTION_TRANSACTIONS)]
        # the check is not broken: a transaction carries a witness
        assert any(tx.is_segwit for tx in txs)

        conn.wait_for_block_announcement(_tip(node))
        _request_cb_announcements(conn, node)

        # the block mined next is announced as a cmpctblock
        conn.clear_block_announcement()
        (block_hash,) = wallet.generate(1, confirm=txs)
        block = _read_block(node, block_hash)
        conn.wait_until(lambda: conn.has("cmpctblock"))
        _check_compactblock_construction(
            _parse_cmpctblock(conn.last("cmpctblock")), block_hash, block
        )

        # and sent as one for a getdata
        conn.clear_block_announcement()
        conn.send(GetData([Inventory(InventoryType.MSG_CMPCT_BLOCK, block_hash)]))
        conn.wait_until(lambda: conn.has("cmpctblock"))
        _check_compactblock_construction(
            _parse_cmpctblock(conn.last("cmpctblock")), block_hash, block
        )


def an_announced_block_is_asked_for_compact(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_compactblock_requests`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 0)
    with ExitStack() as stack:
        conn = _connect(stack, node)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))

        for announce in ("inv", "header"):
            block = build_next_block(node, wallet.script_pub_key)
            block_hash = block.header.hash
            headers = Headers([block.header], check_validity=False)
            if announce == "inv":
                conn.send(Inv([Inventory(InventoryType.MSG_BLOCK, block_hash)]))
                conn.wait_until(lambda: conn.has("getheaders"))
            conn.send(headers)
            conn.wait_for_getdata(block_hash)
            items = GetData.parse(conn.last("getdata").payload).items
            assert items[0].type_code == InventoryType.MSG_CMPCT_BLOCK

            # a cmpctblock leaving the coinbase out, as a short id
            coinbase = block.transactions[0]
            keyed = CmpctBlock(block.header, 0, check_validity=False)
            cmpct = CmpctBlock(
                block.header, 0, [keyed.short_id(coinbase.hash)], check_validity=False
            )
            conn.clear("getblocktxn")
            conn.send_and_ping(cmpct)
            assert _tip(node) == block.header.previous_block_hash
            # is completed by the coinbase the node asks for
            _getblocktxn_expected(conn, block_hash, [0])

            conn.send_and_ping(BlockTxn(block_hash, [coinbase], check_validity=False))
            assert _tip(node) == block_hash


def only_missing_transactions_are_asked_for(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_getblocktxn_requests`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 1)
    with ExitStack() as stack:
        conn = _connect(stack, node)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))
        _make_high_bandwidth(conn, node, wallet)

        def getblocktxn_response(cmpct: CmpctBlock, indexes: Sequence[int]) -> None:
            conn.clear("getblocktxn")
            conn.send_and_ping(cmpct)
            _getblocktxn_expected(conn, cmpct.header.hash, indexes)

        def tip_after_message(payload: Payload, block_hash: bytes) -> None:
            conn.send_and_ping(payload)
            assert _tip(node) == block_hash

        # a cmpctblock not reconstructed: every transaction is asked for
        block, utxo = _chain_block(node, wallet, wallet.get_utxo(), 5)
        block_hash = block.header.hash
        getblocktxn_response(_cmpctblock(block), [1, 2, 3, 4, 5])
        tip_after_message(
            BlockTxn(block_hash, block.transactions[1:], check_validity=False),
            block_hash,
        )

        # the prefilled transactions interspersed
        block, utxo = _chain_block(node, wallet, utxo, 5)
        block_hash = block.header.hash
        getblocktxn_response(_cmpctblock(block, [0, 1, 5]), [2, 3, 4])
        tip_after_message(
            BlockTxn(block_hash, block.transactions[2:5], check_validity=False),
            block_hash,
        )

        # one transaction given ahead: the one not in the mempool is asked
        block, utxo = _chain_block(node, wallet, utxo, 5)
        block_hash = block.header.hash
        conn.send_and_ping(_tx(block.transactions[1]))
        assert block.transactions[1].id.hex() in _mempool(node)
        getblocktxn_response(_cmpctblock(block, [0, 2, 3, 4]), [5])
        tip_after_message(
            BlockTxn(block_hash, [block.transactions[5]], check_validity=False),
            block_hash,
        )

        # every transaction given ahead: the block is reconstructed at once
        block, _ = _chain_block(node, wallet, utxo, 10)
        for tx in block.transactions[1:]:
            conn.send(_tx(tx))
        conn.sync_with_ping()
        node_mempool = _mempool(node)
        for tx in block.transactions[1:]:
            assert tx.id.hex() in node_mempool
        conn.clear("getblocktxn")
        tip_after_message(_cmpctblock(block), block.header.hash)
        assert not conn.has("getblocktxn")


def getblocktxn_is_answered_near_the_tip(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_getblocktxn_handler`, the disconnect's log line aside.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, _MAX_GETBLOCKTXN_DEPTH + 1)
    # each block the requests below read carries transactions
    for _ in range(_MAX_GETBLOCKTXN_DEPTH + 1):
        chain = wallet.send_self_transfer_chain(chain_length=_HANDLER_CHAIN_LENGTH)
        wallet.generate(1, confirm=chain)

    with ExitStack() as stack:
        conn = _connect(stack, node)
        chain_height = node.rpc.call("getblockcount")
        current_height = chain_height
        while current_height >= chain_height - _MAX_GETBLOCKTXN_DEPTH:
            block_hash = bytes.fromhex(node.rpc.call("getblockhash", [current_height]))
            block = _read_block(node, block_hash)
            count = len(block.transactions)
            indexes = sorted(random.sample(range(count), random.randint(1, count)))
            conn.send(GetBlockTxn(block_hash, indexes))
            conn.wait_until(lambda: conn.has("blocktxn"), timeout=10)

            answer = BlockTxn.parse(conn.last("blocktxn").payload, check_validity=False)
            assert answer.block_hash == block_hash
            assert len(answer.transactions) == len(indexes)
            for index, tx in zip(indexes, answer.transactions, strict=True):
                assert tx.id == block.transactions[index].id
                # the witness is the block's own
                assert tx.hash == block.transactions[index].hash
            conn.clear("blocktxn")
            current_height -= 1

        # past the depth, the whole block is sent instead
        block_hash = bytes.fromhex(node.rpc.call("getblockhash", [current_height]))
        conn.clear("block", "blocktxn")
        conn.send_and_ping(GetBlockTxn(block_hash, [0]))
        assert conn.has("block")
        sent = Block.parse(conn.last("block").payload, check_validity=False)
        assert sent.header.hash == block_hash
        assert not conn.has("blocktxn")

        # an index past the block has the node drop the peer
        bad_peer = _connect(stack, node)
        block_hash = bytes.fromhex(node.rpc.call("getblockhash", [chain_height]))
        count = len(_read_block(node, block_hash).transactions)
        bad_peer.send(GetBlockTxn(block_hash, [count]))
        bad_peer.peer.wait_for_disconnect()


def a_block_off_the_tip_is_not_sent_compact(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_compactblocks_not_at_tip`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 0)
    with ExitStack() as stack:
        conn = _connect(stack, node)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))
        _make_high_bandwidth(conn, node, wallet)

        # a block at Core's MAX_CMPCTBLOCK_DEPTH is sent compact
        new_blocks = []
        for _ in range(_MAX_CMPCTBLOCK_DEPTH + 1):
            conn.clear_block_announcement()
            new_blocks += wallet.generate(1)
            conn.wait_until(lambda: conn.block_announced)

        conn.clear_block_announcement()
        conn.send(GetData([Inventory(InventoryType.MSG_CMPCT_BLOCK, new_blocks[0])]))
        conn.wait_until(lambda: conn.has("cmpctblock"))

        # one block deeper, the whole block is sent instead
        conn.clear_block_announcement()
        wallet.generate(1)
        conn.wait_until(lambda: conn.block_announced)
        conn.clear_block_announcement()
        conn.clear("block")
        conn.send(GetData([Inventory(InventoryType.MSG_CMPCT_BLOCK, new_blocks[0])]))
        conn.wait_until(lambda: conn.has("block"))
        sent = Block.parse(conn.last("block").payload, check_validity=False)
        assert sent.header.hash == new_blocks[0]

        # a cmpctblock for a block off the tip leaves its header alone
        cur_height = node.rpc.call("getblockcount")
        parent = bytes.fromhex(node.rpc.call("getblockhash", [cur_height - 5]))
        on_tip = build_next_block(node, wallet.script_pub_key)
        header = mine(replace(on_tip.header, previous_block_hash=parent))
        assert header is not None
        block = Block(header, on_tip.transactions, check_validity=False)
        conn.send_and_ping(_cmpctblock(block))

        (tip,) = [
            tip
            for tip in node.rpc.call("getchaintips")
            if tip["hash"] == block.header.hash.hex()
        ]
        assert tip["status"] == "headers-only"

        # and a getblocktxn for it is left unanswered
        conn.clear("blocktxn")
        conn.send_and_ping(GetBlockTxn(block.header.hash, [0]))
        assert not conn.has("blocktxn")


def a_wrong_blocktxn_falls_back_to_the_block(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_incorrect_blocktxn_response`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 1)
    with ExitStack() as stack:
        conn = _connect(stack, node)
        conn.send_and_ping(SendCmpct(announce=True, version=_VERSION))
        _make_high_bandwidth(conn, node, wallet)

        block, _ = _chain_block(node, wallet, wallet.get_utxo(), 10)
        block_hash = block.header.hash
        # the first five of its transactions are relayed ahead
        for tx in block.transactions[1:6]:
            conn.send(_tx(tx))
        conn.sync_with_ping()
        node_mempool = _mempool(node)
        for tx in block.transactions[1:6]:
            assert tx.id.hex() in node_mempool

        conn.clear("getblocktxn")
        conn.send_and_ping(_cmpctblock(block))
        _getblocktxn_expected(conn, block_hash, [6, 7, 8, 9, 10])

        # a blocktxn carrying a wrong transaction
        wrong = [block.transactions[5], *block.transactions[7:]]
        conn.send_and_ping(BlockTxn(block_hash, wrong, check_validity=False))
        assert _tip(node) == block.header.previous_block_hash

        # has the node ask for the whole block, which it then takes
        conn.wait_for_getdata(block_hash)
        items = GetData.parse(conn.last("getdata").payload).items
        assert items[0].type_code in (
            InventoryType.MSG_BLOCK,
            InventoryType.MSG_WITNESS_BLOCK,
        )
        conn.send_and_ping(_block_payload(block))
        assert _tip(node) == block_hash


def a_submitted_block_is_announced_compact(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `test_end_to_end_block_relay`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, wallet = _node(cluster, skip_counts, 1)
    with ExitStack() as stack:
        listeners = [_connect(stack, node) for _ in range(2)]
        for listener in listeners:
            _request_cb_announcements(listener, node)

        block, _ = _chain_block(node, wallet, wallet.get_utxo(), 10)
        for listener in listeners:
            listener.clear_block_announcement()
        block_hex = block.serialize(include_witness=True, check_validity=False).hex()
        assert node.rpc.call("submitblock", [block_hex]) is None

        for listener in listeners:
            listener.wait_until(partial(listener.has, "cmpctblock"))
            cmpct = _parse_cmpctblock(listener.last("cmpctblock"))
            assert cmpct.header.hash == block.header.hash
