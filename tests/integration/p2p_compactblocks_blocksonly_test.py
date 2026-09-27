# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks_blocksonly`, one body over either node.

Read from Core's `test/functional/p2p_compactblocks_blocksonly.py`
(`bf9884f4e55d`, 2026-06-18): four nodes, the first under `-blocksonly`
(`Capability.BLOCKS_ONLY`), the third the miner (`Capability.MINE`), and
a `Peer` (`peer.py`) on each of the other three delivering the miner's
blocks by hand. A `-blocksonly` node selects no BIP152 high-bandwidth
peer on a new tip, asks for a full block rather than a compact one, still
serves a compact block asked for, and ignores a `cmpctblock` sent to it,
asked for or not, where a node relaying transactions reconstructs one.
The miner's own blocks reach a node through a connection made and
dropped again (`Capability.CONNECT`, `Capability.DISCONNECT`) before
each `cmpctblock` is sent, so that the node holds its parent.

Core's own claim in full, reached another way at the start. Core starts
every node on its cached chain, out of initial block download; this
mines one block on the miner and submits it to the other three, which
takes each out of it. BIP152's messages are btclib's own
`btclib.p2p.compact_blocks`: `SendCmpct`, and `CmpctBlock` built the way
Core's `HeaderAndShortIDs.initialize_from_block` builds one, the
coinbase prefilled and every other transaction a short id of its wtxid.
Whether a `-blocksonly` bitcoind ignores a `cmpctblock` depends on the
build, `_blocksonly_ignores_cmpctblock` below having how it is read.
`p2p_compactblocks_blocksonly_bitcoind_test.py` and
`p2p_compactblocks_blocksonly_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.p2p import (
    BlockPayload,
    CmpctBlock,
    GetData,
    Headers,
    Inventory,
    InventoryType,
    PrefilledTransaction,
    SendCmpct,
)
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import (
    connect_nodes,
    disconnect_nodes,
    wait_until_tips_agree,
)
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message, Payload

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["blocksonly_node_neither_asks_for_nor_takes_compact_blocks"]

_MAGIC = magic_from_chain("regtest")

# Core's own `CLIENT_VERSION` (`src/clientversion.h`), a bitcoind's own
# `getnetworkinfo` `version`, at or past which a `-blocksonly` node
# ignores a `cmpctblock`: `v32.0.0`, the first release carrying
# bitcoin/bitcoin@bf9884f4e55df502b67b2636969cacce62edaee9. A known limit:
# a `master` build from its merge (`69fc991791`, 2026-07-06) until the
# version moved to `32.99` (`f3fec67c3e`, 2026-09-11) reports `319900` and
# ignores one all the same, so this test fails against such a build
_BLOCKSONLY_IGNORES_CMPCTBLOCK_VERSION = 320000


def _build_block_on_tip(miner: BitcoindAdapter | BtclibNodeAdapter) -> Block:
    """Core's own `build_block_on_tip`: mine one block, and read it back."""
    (block_hash,) = miner.mine(1)
    block_hex = miner.rpc.call("getblock", [block_hash, 0])
    # the header's own check defaults to mainnet's proof-of-work limit
    return Block.parse(bytes.fromhex(block_hex), check_validity=False)


def _headers(block: Block) -> Headers:
    """Core's own `msg_headers([block])`, a regtest header unchecked."""
    return Headers([block.header], check_validity=False)


def _block_payload(block: Block) -> BlockPayload:
    """Core's own `msg_block(block)`, witnesses included."""
    return BlockPayload(block, include_witness=True, check_validity=False)


def _cmpctblock(block: Block) -> CmpctBlock:
    """Core's `HeaderAndShortIDs.initialize_from_block`, `use_witness=True`."""
    keyed = CmpctBlock(block.header, check_validity=False)
    coinbase, *rest = block.transactions
    return CmpctBlock(
        block.header,
        keyed.nonce,
        [keyed.short_id(tx.hash) for tx in rest],
        [PrefilledTransaction(0, coinbase)],
        check_validity=False,
    )


def _send_and_ping(peer: Peer, payload: Payload) -> None:
    """Core's own `send_and_ping`: send, then wait out a ping round trip."""
    peer.send(payload, check_validity=False)
    peer.sync_with_ping()


def _connect(node: NodeAdapter) -> Peer:
    """Core's own `add_p2p_connection`: a handshake, then a ping round trip."""
    peer = Peer(node.p2p_address, _MAGIC)
    peer.handshake()
    peer.sync_with_ping()
    return peer


def _last(peer: Peer, command: str) -> Message:
    return peer.last_message[command]


def _cmpctblock_hash(message: Message) -> bytes:
    return CmpctBlock.parse(message.payload, check_validity=False).header.hash


def _ignores_cmpctblock(
    miner: BitcoindAdapter | BtclibNodeAdapter,
    node: NodeAdapter,
    peer: Peer,
    *,
    solicited: bool,
) -> bool:
    """Core's own `ignores_cmpctblock`, over `peer`'s own connection to `node`.

    The miner is connected and dropped again first, so that `node` holds
    the parent of the block the `cmpctblock` then announces; a block the
    node ignores is sent whole afterwards, keeping it on the miner's tip.
    """
    connect_nodes(miner, node)
    wait_until_tips_agree([miner, node], timeout=10)
    disconnect_nodes(miner, node)

    block = _build_block_on_tip(miner)
    if solicited:
        peer.send(_headers(block), check_validity=False)
        peer.wait_for(
            "getdata",
            predicate=lambda m: any(
                item.hash == block.header.hash
                for item in GetData.parse(m.payload).items
            ),
            timeout=10,
        )
    _send_and_ping(peer, _cmpctblock(block))

    received = node.rpc.call("getbestblockhash") == block.header.hash.hex()
    if not received:
        _send_and_ping(peer, _block_payload(block))
    return not received


def _blocksonly_ignores_cmpctblock(node: NodeAdapter) -> bool:
    """Whether `node`, under `-blocksonly`, ignores a `cmpctblock`.

    Core's own claim for every node, bitcoind before
    `_BLOCKSONLY_IGNORES_CMPCTBLOCK_VERSION` excepted: that build
    reconstructs the block, read off its own `getnetworkinfo` `version`
    ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
    """
    if not isinstance(node, BitcoindAdapter):
        return True
    version = node.rpc.call("getnetworkinfo")["version"]
    return bool(version >= _BLOCKSONLY_IGNORES_CMPCTBLOCK_VERSION)


def blocksonly_node_neither_asks_for_nor_takes_compact_blocks(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    blocksonly, high_bw_node, miner, low_bw_node = cluster(4)
    require(Capability.BLOCKS_ONLY, blocksonly.capabilities, skip_counts)
    require(Capability.MINE, miner.capabilities, skip_counts)
    require(Capability.CONNECT, miner.capabilities, skip_counts)
    require(Capability.DISCONNECT, miner.capabilities, skip_counts)
    blocksonly.restart(["-blocksonly"])

    # a node selects a high-bandwidth peer only once out of IBD
    (first_hash,) = miner.mine(1)
    first_hex = miner.rpc.call("getblock", [first_hash, 0])
    for node in (blocksonly, high_bw_node, low_bw_node):
        assert node.rpc.call("submitblock", [first_hex]) is None
    for node in (blocksonly, high_bw_node, miner, low_bw_node):
        assert not node.rpc.call("getblockchaininfo")["initialblockdownload"]

    conn_blocksonly = _connect(blocksonly)
    conn_high_bw = _connect(high_bw_node)
    conn_low_bw = _connect(low_bw_node)
    try:
        for conn in (conn_blocksonly, conn_high_bw, conn_low_bw):
            assert conn.message_count["sendcmpct"] == 1
            _send_and_ping(conn, SendCmpct(announce=False, version=2))

        # no -blocksonly node selects a peer for high-bandwidth mode
        block0 = _build_block_on_tip(miner)
        block0_hex = block0.header.hash.hex()
        _send_and_ping(conn_blocksonly, _block_payload(block0))
        assert blocksonly.rpc.call("getbestblockhash") == block0_hex
        assert conn_blocksonly.message_count["sendcmpct"] == 1
        announce = SendCmpct.parse(_last(conn_blocksonly, "sendcmpct").payload)
        assert announce.announce is False

        # a node relaying transactions selects the peer that sent the tip
        _send_and_ping(conn_high_bw, _block_payload(block0))
        assert high_bw_node.rpc.call("getbestblockhash") == block0_hex
        while conn_high_bw.message_count["sendcmpct"] < 2:
            conn_high_bw.wait_for("sendcmpct")
        assert conn_high_bw.message_count["sendcmpct"] == 2
        announce = SendCmpct.parse(_last(conn_high_bw, "sendcmpct").payload)
        assert announce.announce is True

        # the low-bandwidth node gets block 0 from no peer, so selects none
        assert (
            low_bw_node.rpc.call(
                "submitblock", [block0.serialize(check_validity=False).hex()]
            )
            is None
        )

        # a -blocksonly node asks for a full block, not a compact one
        block1 = _build_block_on_tip(miner)
        _send_and_ping(conn_blocksonly, _headers(block1))
        getdata = GetData.parse(_last(conn_blocksonly, "getdata").payload)
        assert getdata.items == (
            Inventory(InventoryType.MSG_WITNESS_BLOCK, block1.header.hash),
        )

        _send_and_ping(conn_high_bw, _headers(block1))
        getdata = GetData.parse(_last(conn_high_bw, "getdata").payload)
        assert getdata.items == (
            Inventory(InventoryType.MSG_CMPCT_BLOCK, block1.header.hash),
        )
        # the block itself, so that the peer is not stalled later on
        block1_cmpct = _cmpctblock(block1)
        _send_and_ping(conn_high_bw, block1_cmpct)

        # low bandwidth, and no -blocksonly node: a compact block is asked for
        _send_and_ping(conn_low_bw, _headers(block1))
        getdata = GetData.parse(_last(conn_low_bw, "getdata").payload)
        assert getdata.items == (
            Inventory(InventoryType.MSG_CMPCT_BLOCK, block1.header.hash),
        )
        _send_and_ping(conn_low_bw, block1_cmpct)

        # a -blocksonly node still serves a compact block
        conn_blocksonly.send(
            GetData([Inventory(InventoryType.MSG_CMPCT_BLOCK, block0.header.hash)])
        )
        conn_blocksonly.wait_for(
            "cmpctblock", predicate=lambda m: _cmpctblock_hash(m) == block0.header.hash
        )

        # and announces one to a peer asking for high-bandwidth mode
        _send_and_ping(conn_blocksonly, SendCmpct(announce=True, version=2))
        block2 = _build_block_on_tip(miner)
        for block in (block1, block2):
            assert (
                blocksonly.rpc.call(
                    "submitblock", [block.serialize(check_validity=False).hex()]
                )
                is None
            )
        conn_blocksonly.wait_for(
            "cmpctblock", predicate=lambda m: _cmpctblock_hash(m) == block2.header.hash
        )

        # a node relaying transactions takes a high-bandwidth peer's
        assert not _ignores_cmpctblock(
            miner, high_bw_node, conn_high_bw, solicited=False
        )
        # a -blocksonly node ignores one
        ignores = _blocksonly_ignores_cmpctblock(blocksonly)
        assert (
            _ignores_cmpctblock(miner, blocksonly, conn_blocksonly, solicited=False)
            is ignores
        )
        # a low-bandwidth node takes one it asked for
        assert not _ignores_cmpctblock(miner, low_bw_node, conn_low_bw, solicited=True)
        # a -blocksonly node ignores one even where it asked for the block
        assert (
            _ignores_cmpctblock(miner, blocksonly, conn_blocksonly, solicited=True)
            is ignores
        )
    finally:
        for conn in (conn_blocksonly, conn_high_bw, conn_low_bw):
            conn.close()
