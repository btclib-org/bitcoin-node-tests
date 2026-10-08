# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_node_network_limited`, one body over either node.

Read from Core's `test/functional/p2p_node_network_limited.py`
(`fa7bac94d87a`, 2026-03-12): three nodes, the first under `-prune=550`.
The pruned node signals `NODE_NETWORK_LIMITED` and not `NODE_NETWORK`,
in its `version` to a `Peer` (`peer.py`) and in `getnetworkinfo`'s
`localservices`; it serves a `getdata` for a block within 288 + 2 of its
tip and disconnects the peer asking for one older. A node in initial
block download does not sync from it, and one out of it does. A full
node catching up from it asks only for the blocks within that window,
and syncs the rest from a node that is not pruned.

The nodes mine (`Capability.MINE`), are connected and disconnected
(`Capability.CONNECT`, `Capability.DISCONNECT`), and the full node's
own networking is suspended and resumed over `setnetworkactive`
(`Capability.SUSPEND_NETWORK`). `-prune` asks for no capability:
`cli.py` registers it, at btclib-node's released `2026.9.24` and at its
`main` alike.

Core's own claim in full. Core adds `NODE_P2P_V2` to the services it
expects where its run passes `--v2transport`, which starts every node
with `-v2transport=1`; this harness passes no `-v2transport`, so the
bit is expected where the node declares `Capability.V2TRANSPORT`. That
reads the capability as BIP324 on by default, which it is on bitcoind
(`-v2transport` defaults to on) and not what the capability itself
promises: it names BIP324 accepted from another node, not offered
unasked.

`p2p_node_network_limited_bitcoind_test.py` and
`p2p_node_network_limited_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from bitcoin_core_rpc import RpcError, magic_from_chain
from btclib.p2p import GetData, Inventory, ServiceFlags
from btclib.p2p.data import BlockPayload
from btclib.p2p.inventory import InventoryType

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import (
    connect_nodes,
    disconnect_nodes,
    sync_all,
    wait_until,
    wait_until_tips_agree,
)
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["node_network_limited"]

_MAGIC = magic_from_chain("regtest")

# Core's own `NODE_NETWORK_LIMITED_MIN_BLOCKS`
_NODE_NETWORK_LIMITED_MIN_BLOCKS = 288

# how many blocks one `mine` call asks for, as `rpc_getblockfrompeer_test`
# chunks them: a bitcoind's own `generatetoaddress` answers only once
# every block is mined
_MINE_CHUNK = 50

_NOT_DOWNLOADED = "Block not available (not fully downloaded)"


def _mine(node: BitcoindAdapter | BtclibNodeAdapter, count: int) -> list[str]:
    """Mine `count` blocks on `node`, at most `_MINE_CHUNK` per call."""
    hashes: list[str] = []
    while len(hashes) < count:
        hashes += node.mine(min(count - len(hashes), _MINE_CHUNK))
    return hashes


def _request_block(peer: Peer, block_hash: str) -> None:
    """Core's own `P2PIgnoreInv.send_getdata_for_block`."""
    peer.send(GetData([Inventory(InventoryType.MSG_BLOCK, bytes.fromhex(block_hash))]))


def _is_block(block_hash: str) -> Callable[[Message], bool]:
    """Match a `block` message carrying `block_hash`."""
    wanted = bytes.fromhex(block_hash)

    def _matches(message: Message) -> bool:
        block = BlockPayload.parse(message.payload, check_validity=False).block
        return block.header.hash == wanted

    return _matches


def _not_downloaded(node: NodeAdapter, block_hash: str) -> bool:
    """Core's own `try_rpc` over `getblock`: whether the block is missing."""
    try:
        node.rpc.call("getblock", [block_hash])
    except RpcError as err:
        if err.code == -1 and _NOT_DOWNLOADED in str(err):
            return True
        raise
    return False


def _chain_tip_status(node: NodeAdapter, block_hash: str) -> str:
    """Return `getchaintips`' status for `block_hash`, `""` where absent."""
    for tip in node.rpc.call("getchaintips"):
        if tip["hash"] == block_hash:
            return str(tip["status"])
    return ""


def _avoid_requesting_historical_blocks(
    pruned_node: BitcoindAdapter | BtclibNodeAdapter,
    miner: BitcoindAdapter | BtclibNodeAdapter,
    full_node: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Core's own `test_avoid_requesting_historical_blocks`."""
    # connect and mine a block, so that no node is in initial block download
    connect_nodes(miner, pruned_node)
    connect_nodes(miner, full_node)
    miner.mine(1)
    sync_all([pruned_node, miner, full_node])
    for node in (pruned_node, miner, full_node):
        assert not node.rpc.call("getblockchaininfo")["initialblockdownload"]

    # isolate the full node, which stays out of initial block download
    full_node.rpc.call("setnetworkactive", [False])
    wait_until(lambda: len(full_node.rpc.call("getpeerinfo")) == 0)

    # past the threshold, blocks deeper than it being historical ones
    _mine(miner, _NODE_NETWORK_LIMITED_MIN_BLOCKS + 12)
    wait_until_tips_agree([miner, pruned_node])

    # the full node, behind, stays connected to the pruned one
    start_height_full_node = full_node.rpc.call("getblockcount")
    full_node.rpc.call("setnetworkactive", [True])
    connect_nodes(full_node, pruned_node)
    assert len(full_node.rpc.call("getpeerinfo")) == 1

    # until the full node holds every header
    best_block_hash = pruned_node.rpc.call("getbestblockhash")
    wait_until(lambda: _chain_tip_status(full_node, best_block_hash) == "headers-only")

    # it asks only for the blocks within the threshold, with a two-block
    # buffer, and for no historical one; the tip first, to avoid a race
    tip_height = pruned_node.rpc.call("getblockcount")
    limit_buffer = 2
    wait_until(lambda: not _not_downloaded(full_node, best_block_hash))
    for height in range(start_height_full_node + 1, tip_height + 1):
        block_hash = pruned_node.rpc.call("getblockhash", [height])
        if height <= tip_height - (_NODE_NETWORK_LIMITED_MIN_BLOCKS - limit_buffer):
            assert _not_downloaded(full_node, block_hash)
        else:
            assert not _not_downloaded(full_node, block_hash)

    # not synced, until connected to a full node that has the rest
    assert full_node.rpc.call("getblockcount") == start_height_full_node
    connect_nodes(full_node, miner)
    wait_until_tips_agree([miner, full_node], timeout=60)


def node_network_limited(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    pruned_node, miner, full_node = cluster(3)
    require(Capability.MINE, miner.capabilities, skip_counts)
    require(Capability.MINE, pruned_node.capabilities, skip_counts)
    require(Capability.CONNECT, pruned_node.capabilities, skip_counts)
    require(Capability.DISCONNECT, pruned_node.capabilities, skip_counts)
    require(Capability.SUSPEND_NETWORK, full_node.capabilities, skip_counts)
    pruned_node.restart(["-prune=550"])

    expected_services = ServiceFlags.NODE_WITNESS | ServiceFlags.NODE_NETWORK_LIMITED
    if Capability.V2TRANSPORT in pruned_node.capabilities:
        expected_services |= ServiceFlags.NODE_P2P_V2

    with Peer(pruned_node.p2p_address, _MAGIC) as peer:
        version = peer.handshake()
        peer.sync_with_ping()

        # the services signalled, and `localservices`
        assert version.services == expected_services
        localservices = pruned_node.rpc.call("getnetworkinfo")["localservices"]
        assert int(localservices, 16) == expected_services

        # enough blocks to reach the NODE_NETWORK_LIMITED range
        connect_nodes(pruned_node, miner)
        blocks = _mine(miner, 292)
        wait_until_tips_agree([pruned_node, miner])

        # the block at tip - 290 is the last one served
        _request_block(peer, blocks[1])
        peer.wait_for("block", predicate=_is_block(blocks[1]), timeout=3)

        # and asking for the one before it is a disconnect
        _request_block(peer, blocks[0])
        peer.wait_for_disconnect(timeout=5)

    # the full node, in initial block download, does not sync from the
    # pruned one
    connect_nodes(pruned_node, full_node)
    with contextlib.suppress(TimeoutError):
        wait_until_tips_agree([pruned_node, full_node], timeout=5)
    best = full_node.rpc.call("getbestblockhash")
    assert full_node.rpc.call("getblockheader", [best])["height"] == 0

    # and does once connected to the node that is not pruned
    connect_nodes(miner, full_node)
    wait_until_tips_agree([pruned_node, miner, full_node], timeout=60)

    disconnect_nodes(pruned_node, miner)
    disconnect_nodes(pruned_node, full_node)
    disconnect_nodes(miner, full_node)

    # a node out of initial block download syncs from the pruned one
    _mine(pruned_node, 10)
    connect_nodes(pruned_node, miner)
    wait_until_tips_agree([pruned_node, miner], timeout=60)

    _avoid_requesting_historical_blocks(pruned_node, miner, full_node)
