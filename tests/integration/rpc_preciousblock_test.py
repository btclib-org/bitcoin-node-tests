# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_preciousblock`, one body over either node.

Read from Core's `test/functional/rpc_preciousblock.py` (`fa5f29774872`,
2025-12-16), a file needing no mechanism the adapter lacks
([ISS 317](https://github.com/btclib-org/bitcoin-node-tests/issues/317)):
`preciousblock` (`Capability.PRECIOUS_BLOCK`) has a node take a block as
if it had received it before every other block of the same work. The
nodes start unlinked on a clean chain, and each mines blocks of its own
(`Capability.GENERATE`). Handed each other's blocks over `submitblock`,
the first node reorgs to the second node's longer chain. The first and
the second node then each mine a branch of equal length on it, and
neither reorgs once handed the other's branch and linked to it
(`Capability.CONNECT`): `preciousblock` moves each to the other's tip
and back. A block the first node mines on the second node's branch takes
the second node to it, and `preciousblock` on the first node's branch no
longer moves it. The third node mines a branch as long as that chain;
linked, the second node keeps its tip and the third its own, until
`preciousblock` names the other's.

What differs from Core's file:

- Core's `generate` has each node pay its own `PRIV_KEYS` address, and
  so does this body, through `generatetoaddress`, so that two nodes
  mining at one height mine different blocks;
- Core's `unidirectional_node_sync_via_rpc` takes any exception raised
  while it reads a block as the sign that the block is missing; this
  body takes `RpcError` alone.

Every step is the same at `v31.1`, the release `bitcoind.py` pins, whose
copy of the file is the pin's.

`rpc_preciousblock_bitcoind_test.py` and
`rpc_preciousblock_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import RpcError

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_tips_agree

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["a_precious_block_wins_a_tie"]

type _Node = BitcoindAdapter | BtclibNodeAdapter

# Core's own `PRIV_KEYS` addresses (`test_framework/test_node.py`), the
# one its `generate` has each node pay, by the node's own index
_ADDRESSES = (
    "mjTkW3DjgyZck4KbiRusZsqTgaYTxdSz6z",
    "msX6jQXvxiNhx3Q62PKeLPrhrqZQdSimTg",
    "mnonCMyH9TmAsSj3M59DsbH8H63U3RKoFP",
)

# Core's own `sync_blocks` default timeout
_SYNC_TIMEOUT = 60.0


def _generate(node: NodeAdapter, index: int, count: int) -> str:
    """Core's own `generate(node, count)`: pay the node's own address.

    :return: the hash of the last block mined.
    """
    hashes = node.rpc.call("generatetoaddress", [count, _ADDRESSES[index]])
    assert isinstance(hashes, list)
    last = hashes[-1]
    assert isinstance(last, str)
    return last


def _best(node: NodeAdapter) -> str:
    """Return `getbestblockhash`'s own answer."""
    best = node.rpc.call("getbestblockhash")
    assert isinstance(best, str)
    return best


def _count(node: NodeAdapter) -> int:
    """Return `getblockcount`'s own answer."""
    count = node.rpc.call("getblockcount")
    assert isinstance(count, int)
    return count


def _has_block(node: NodeAdapter, block_hash: str) -> bool:
    """Tell whether `node` answers `getblock` for `block_hash`."""
    try:
        block = node.rpc.call("getblock", [block_hash, 0])
    except RpcError:
        return False
    assert isinstance(block, str)
    return len(block) > 0


def _unidirectional_sync(source: NodeAdapter, dest: NodeAdapter) -> None:
    """Core's own `unidirectional_node_sync_via_rpc`.

    Submit to `dest`, oldest first, every block of `source`'s own active
    chain that `dest` does not have.
    """
    to_copy: list[str] = []
    block_hash = _best(source)
    while not _has_block(dest, block_hash):
        to_copy.append(block_hash)
        header = source.rpc.call("getblockheader", [block_hash, True])
        assert isinstance(header, dict)
        block_hash = header["previousblockhash"]
    for block_hash in reversed(to_copy):
        block = source.rpc.call("getblock", [block_hash, 0])
        assert dest.rpc.call("submitblock", [block]) in {None, "inconclusive"}


def _sync_via_rpc(nodes: Sequence[NodeAdapter]) -> None:
    """Core's own `node_sync_via_rpc`: every node's chain to every other."""
    for source in nodes:
        for dest in nodes:
            if source is not dest:
                _unidirectional_sync(source, dest)


def _precious(node: NodeAdapter, block_hash: str) -> None:
    """Ask `node` to take `block_hash` as received first."""
    node.rpc.call("preciousblock", [block_hash])


def a_precious_block_wins_a_tie(
    cluster: Callable[[int], Sequence[_Node]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `setup_network` and `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    nodes = cluster(3)
    node0, node1, node2 = nodes
    for node in nodes:
        require(Capability.PRECIOUS_BLOCK, node.capabilities, skip_counts)
    for node in nodes:
        require(Capability.GENERATE, node.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node1.capabilities, skip_counts)

    # submitblock can in principle reorg to a competing chain
    _generate(node0, 0, 1)
    assert _count(node0) == 1
    hash_z = _generate(node1, 1, 2)
    assert _count(node1) == 2
    _sync_via_rpc(nodes)
    assert _best(node0) == hash_z

    # blocks A-B-C on the first node, competing blocks E-F-G on the second
    hash_c = _generate(node0, 0, 3)
    assert _count(node0) == 5
    hash_g = _generate(node1, 1, 3)
    assert _count(node1) == 5
    assert hash_c != hash_g

    # linked, neither reorgs: the blocks are submitted over RPC first, so
    # that any reorg happens before the check
    _sync_via_rpc(nodes[:2])
    connect_nodes(node0, node1)
    assert _best(node0) == hash_c
    assert _best(node1) == hash_g

    _precious(node0, hash_g)
    assert _best(node0) == hash_g
    _precious(node0, hash_c)
    assert _best(node0) == hash_c
    _precious(node1, hash_c)
    wait_until_tips_agree(nodes[:2], timeout=_SYNC_TIMEOUT)
    assert _best(node1) == hash_c
    _precious(node1, hash_g)
    assert _best(node1) == hash_g
    _precious(node0, hash_g)
    assert _best(node0) == hash_g
    _precious(node1, hash_c)
    assert _best(node1) == hash_c

    # (E-F-G-)H on the first node reorgs the second
    _generate(node0, 0, 1)
    assert _count(node0) == 6
    wait_until_tips_agree(nodes[:2], timeout=_SYNC_TIMEOUT)
    hash_h = _best(node0)
    assert _best(node1) == hash_h

    # the second node can no longer prefer C
    _precious(node1, hash_c)
    assert _best(node1) == hash_h

    # competing blocks I-J-K-L on the third node, and no reorg once linked
    _generate(node2, 2, 4)
    assert _count(node2) == 6
    hash_l = _best(node2)
    _sync_via_rpc(nodes[1:])
    connect_nodes(node1, node2)
    connect_nodes(node0, node2)
    assert _best(node0) == hash_h
    assert _best(node1) == hash_h
    assert _best(node2) == hash_l

    _precious(node1, hash_l)
    assert _best(node1) == hash_l
    _precious(node2, hash_h)
    assert _best(node2) == hash_h
