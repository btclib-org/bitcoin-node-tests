# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_headers_sync_with_minchainwork`, one body over either node.

Read from Core's `test/functional/p2p_headers_sync_with_minchainwork.py`
(`ff3e2e4ebdce`, 2026-08-19), an option, the log and the clock beside
node-linking
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
the first node dials each of the others, the second under
`-minimumchainwork=0x1f`, the third and the last under `0x1000`
(`Capability.MINIMUM_CHAIN_WORK`), the last giving the first `noban`.
While the chain the first node mines (`Capability.GENERATE`) has less
work than a node's floor, that node's log reads "Ignoring low-work
chain" at the chain's height, and it keeps the genesis block as its only
chain tip; the last node logs "Synchronizing blockheaders" at that
height instead (`Capability.DEBUG_LOG`), and holds the chain as a
headers-only tip. Once the chain has the work a floor names, the node
under it syncs. The first and the second node, disconnected
(`Capability.DISCONNECT`), each mine a chain of their own past the next
locator entry, and once reconnected, their clocks held
(`Capability.CLOCK`), every node syncs. A peer sending the first node
headers forking from genesis, with less work than its chain, is
reported by `getpeerinfo` with every one of them presynced. With the
first node's clock set more than `MAX_FUTURE_BLOCK_TIME` behind the
genesis block's median time, the same headers from a new peer make it
abort and say why on stderr.

What differs from Core's file:

- Core's harness starts each node under its own `extra_args`; this
  harness's nodes start without, and each is restarted under Core's
  before any is connected;
- Core's `generate` asks `generatetoaddress` for every block in one
  call; here `_MINE_CHUNK` blocks at a time, to the same address, the
  mining node's own of `TestNode.PRIV_KEYS`
  (`test_framework/test_node.py`);
- Core builds the headers the peer sends from `getblocktemplate`; here
  their height is one past the first node's `getblockcount`, their time
  one past its `getblockchaininfo` `mediantime` or the wall clock,
  whichever is later, and their version btclib's own
  (`btclib.block.build.build_block`);
- Core's last step, a lagging clock aborting the headers presync, runs
  where the running build's `getnetworkinfo` `version` is `v32.0` or
  later, the first release carrying Core's change
  (bitcoin/bitcoin#35351). A release before it keeps presyncing and
  asks the peer for the headers after the last one sent, which is what
  Core's first commit of that change checks, and what is checked here.
  The threshold misreads a `master` build reporting `31.99` taken after
  the change's merge, bitcoin/bitcoin@58dfcf29f6da5af5e26a4a927df401baed766d5c,
  and before the move to `32.99`,
  bitcoin/bitcoin@f3fec67c3eeb27d5be1bc9d57ca737b74fcd762d: such a build
  aborts, and this test fails against it.

`p2p_headers_sync_with_minchainwork_bitcoind_test.py` and
`p2p_headers_sync_with_minchainwork_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.limits import MAX_FUTURE_BLOCK_TIME
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import GetHeaders, Headers
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
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
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["low_work_headers_are_ignored_until_the_chain_has_the_work"]

type _Node = BitcoindAdapter | BtclibNodeAdapter

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# Core's own `extra_args`, one entry per node
_EXTRA_ARGS = (
    ("-minimumchainwork=0x0", "-checkblockindex=0"),
    ("-minimumchainwork=0x1f", "-checkblockindex=0"),
    ("-minimumchainwork=0x1000", "-checkblockindex=0"),
    (
        "-minimumchainwork=0x1000",
        "-checkblockindex=0",
        "-whitelist=noban@127.0.0.1",
    ),
)

# Core's own `NODE1_BLOCKS_REQUIRED` and `NODE2_BLOCKS_REQUIRED`: the
# heights whose work meets the second node's floor and the third's
_NODE1_BLOCKS_REQUIRED = 15
_NODE2_BLOCKS_REQUIRED = 2047

# Core's own `BLOCKS_TO_MINE`, past the locator entry `T-4104`
_BLOCKS_TO_MINE = 4110

# the height Core's presync step makes sure the first node's chain has,
# and how many headers its peer sends
_PRESYNC_HEIGHT = 3000
_PRESYNC_HEADERS = 2000

# Core's own `PRIV_KEYS[0]` and `PRIV_KEYS[1]` addresses
# (`test_framework/test_node.py`), which its `generate` has the first
# and the second node pay
_ADDRESSES = (
    "mjTkW3DjgyZck4KbiRusZsqTgaYTxdSz6z",
    "msX6jQXvxiNhx3Q62PKeLPrhrqZQdSimTg",
)

# how many blocks one `generatetoaddress` call asks for: it answers only
# once every block is mined, and has to inside the RPC client's own
# timeout (`timeout_factor.rpc_client_timeout`)
_MINE_CHUNK = 100

# Core's own `timeout=2` on each `assert_debug_log`
_LOG_TIMEOUT = 2.0

# Core's own `sync_blocks` default timeout, and the one it gives the
# reorg
_SYNC_TIMEOUT = 60.0
_REORG_SYNC_TIMEOUT = 300.0

# regtest's genesis block, as Core's own test spells its hash
_GENESIS_HASH = "0f9188f13cb7b2c71f2a335e3a4fc328bf5beb436012afca590b1a11466e2206"
_GENESIS_TIP = {
    "height": 0,
    "hash": _GENESIS_HASH,
    "branchlen": 0,
    "status": "active",
}

# what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"

# the `CLIENT_VERSION` (`src/clientversion.h`) of `v32.0`, the first
# release aborting a headers presync its clock lags (bitcoin/bitcoin#35351)
_ABORT_VERSION = 320000

# Core's own `expected_ret_code` for that abort: Unix, Windows native,
# Windows cross builds
_ABORT_EXIT_CODES = (-6, 3, 0xC0000409)

# Core's own `expected_stderr` for that abort
_ABORT_STDERR = "Failure when attempting to initiate headers sync: System clock"

# Core's own `wait_for_getheaders` timeout on a release before it
_GETHEADERS_TIMEOUT = 30.0


def _debug_log(node: _Node) -> Path:
    """Return the log a check reads, `Capability.DEBUG_LOG`'s fact.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def _generate(node: NodeAdapter, address: str, count: int) -> None:
    """Core's own `generate` with `sync_fun=self.no_op`, `count` blocks."""
    while count > 0:
        chunk = min(count, _MINE_CHUNK)
        node.rpc.call("generatetoaddress", [chunk, address])
        count -= chunk


def _block_count(node: NodeAdapter) -> int:
    """Return `getblockcount`'s own answer."""
    count = node.rpc.call("getblockcount")
    assert isinstance(count, int)
    return count


def _best_block_hash(node: NodeAdapter) -> str:
    """Return `getbestblockhash`'s own answer."""
    block_hash = node.rpc.call("getbestblockhash")
    assert isinstance(block_hash, str)
    return block_hash


def _chain_tips(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `getchaintips`'s own answer."""
    tips = node.rpc.call("getchaintips")
    assert isinstance(tips, list)
    return tips


def _check_node3_chaintips(
    node3: NodeAdapter, num_tips: int, tip_hash: str, height: int
) -> None:
    """Core's own `check_node3_chaintips`: the headers-only tip is there."""
    node3_chaintips = _chain_tips(node3)
    assert len(node3_chaintips) == num_tips
    assert {
        "height": height,
        "hash": tip_hash,
        "branchlen": height,
        "status": "headers-only",
    } in node3_chaintips


def _connect_all(nodes: Sequence[NodeAdapter]) -> None:
    """Core's own `reconnect_all`: the first node dials each of the others."""
    for node in nodes[1:]:
        connect_nodes(nodes[0], node)


def _disconnect_all(nodes: Sequence[NodeAdapter]) -> None:
    """Core's own `disconnect_all`."""
    for node in nodes[1:]:
        disconnect_nodes(nodes[0], node)


def _mocktime_all(nodes: Sequence[NodeAdapter], timestamp: int) -> None:
    """Core's own `mocktime_all`."""
    for node in nodes:
        node.set_mock_time(timestamp)


def _chains_sync_when_long_enough(nodes: Sequence[_Node]) -> None:
    """Core's own `test_chains_sync_when_long_enough`."""
    node0, node1, node2, node3 = nodes

    # a chain below every floor but the first node's: ignored by the
    # second and the third, taken as headers by the fourth
    with ExitStack() as logs:
        for node, message in (
            (node1, "[net] Ignoring low-work chain (height=14)"),
            (node2, "[net] Ignoring low-work chain (height=14)"),
            (node3, "Synchronizing blockheaders, height: 14"),
        ):
            logs.enter_context(
                assert_debug_log(_debug_log(node), [message], timeout=_LOG_TIMEOUT)
            )
        _generate(node0, _ADDRESSES[0], _NODE1_BLOCKS_REQUIRED - 1)

    _check_node3_chaintips(
        node3, 2, _best_block_hash(node0), _NODE1_BLOCKS_REQUIRED - 1
    )
    for node in (node1, node2):
        chaintips = _chain_tips(node)
        assert len(chaintips) == 1
        assert _GENESIS_TIP in chaintips

    # the second node's floor met, the third's not
    with ExitStack() as logs:
        for node, message in (
            (node2, "[net] Ignoring low-work chain (height=15)"),
            (node3, "Synchronizing blockheaders, height: 15"),
        ):
            logs.enter_context(
                assert_debug_log(_debug_log(node), [message], timeout=_LOG_TIMEOUT)
            )
        _generate(node0, _ADDRESSES[0], _NODE1_BLOCKS_REQUIRED - _block_count(node0))
    wait_until_tips_agree([node0, node1], timeout=_SYNC_TIMEOUT)

    assert _GENESIS_TIP in _chain_tips(node2)
    assert len(_chain_tips(node2)) == 1
    _check_node3_chaintips(node3, 2, _best_block_hash(node0), _NODE1_BLOCKS_REQUIRED)

    # every floor met, and every node syncs
    _generate(node0, _ADDRESSES[0], _NODE2_BLOCKS_REQUIRED - _block_count(node0))
    wait_until_tips_agree(nodes, timeout=_SYNC_TIMEOUT)


def _large_reorgs_can_succeed(nodes: Sequence[_Node]) -> None:
    """Core's own `test_large_reorgs_can_succeed`."""
    node0, node1 = nodes[:2]
    sync_all(nodes, timeout=_SYNC_TIMEOUT)
    _disconnect_all(nodes)

    _generate(node0, _ADDRESSES[0], _BLOCKS_TO_MINE)
    _generate(node1, _ADDRESSES[1], _BLOCKS_TO_MINE + 2)

    _connect_all(nodes)

    # the clocks held, so that no timeout inside the node fires
    _mocktime_all(nodes, int(time.time()))
    wait_until_tips_agree(nodes, timeout=_REORG_SYNC_TIMEOUT)
    _mocktime_all(nodes, 0)


def _header(previous: bytes, height: int, block_time: int) -> Block:
    """Core's own `create_block(hashprev, tmpl=...)`, solved."""
    coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
    candidate = build_block(
        previous,
        [coinbase],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(candidate.header)
    assert solved is not None
    return Block(solved, candidate.transactions, check_validity=False)


def _aborts_on_a_lagging_clock(node: NodeAdapter) -> bool:
    """Whether `node` aborts a headers presync its clock lags.

    Core's own claim for every node, bitcoind before `_ABORT_VERSION`
    excepted, read off its own `getnetworkinfo` `version`.
    """
    if not isinstance(node, BitcoindAdapter):
        return True
    info = node.rpc.call("getnetworkinfo")
    assert isinstance(info, dict)
    return bool(info["version"] >= _ABORT_VERSION)


def _peerinfo_includes_headers_presync_height(nodes: Sequence[_Node]) -> None:
    """Core's own `test_peerinfo_includes_headers_presync_height`."""
    _disconnect_all(nodes)
    node = nodes[0]

    with Peer(node.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.sync_with_ping()

        # a long chain already
        current_height = _block_count(node)
        if current_height < _PRESYNC_HEIGHT:
            _generate(node, _ADDRESSES[0], _PRESYNC_HEIGHT - current_height)

        # headers forking from genesis, at the chain's next height and time
        chain_info = node.rpc.call("getblockchaininfo")
        assert isinstance(chain_info, dict)
        block_time = max(chain_info["mediantime"] + 1, int(time.time()))
        height = _block_count(node) + 1
        genesis_hash = node.rpc.call("getblockhash", [0])
        assert isinstance(genesis_hash, str)
        previous = bytes.fromhex(genesis_hash)
        new_blocks = []
        for _ in range(_PRESYNC_HEADERS):
            block = _header(previous, height, block_time)
            new_blocks.append(block.header)
            previous = block.header.hash
        peer.send(Headers(new_blocks))
        peer.sync_with_ping()

        # a sync in progress
        peers = node.rpc.call("getpeerinfo")
        assert isinstance(peers, list)
        assert peers[0]["presynced_headers"] == _PRESYNC_HEADERS

    # the same headers from a new peer, the clock lagging the genesis
    # block's median time by more than `MAX_FUTURE_BLOCK_TIME`
    aborts = _aborts_on_a_lagging_clock(node)
    wait_until(lambda: node.rpc.call("getpeerinfo") == [])
    genesis = node.rpc.call("getblockheader", [genesis_hash])
    assert isinstance(genesis, dict)
    node.set_mock_time(genesis["mediantime"] - MAX_FUTURE_BLOCK_TIME - 1)
    with Peer(node.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.sync_with_ping()
        peer.send(Headers(new_blocks))
        if aborts:
            exit_code, stderr = node.wait_until_stopped()
            assert exit_code in _ABORT_EXIT_CODES
            assert _ABORT_STDERR in stderr
        else:
            peer.wait_for(
                "getheaders",
                predicate=lambda m: GetHeaders.parse(m.payload).locator[0] == previous,
                timeout=_GETHEADERS_TIMEOUT,
            )


def low_work_headers_are_ignored_until_the_chain_has_the_work(
    cluster: Callable[[int], Sequence[_Node]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `setup_network` and `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    nodes = cluster(4)
    node0, node1 = nodes[:2]
    for node in nodes:
        require(Capability.MINIMUM_CHAIN_WORK, node.capabilities, skip_counts)
    require(Capability.GENERATE, node0.capabilities, skip_counts)
    require(Capability.GENERATE, node1.capabilities, skip_counts)
    for node in nodes[1:]:
        require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    for node in nodes:
        require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.DISCONNECT, node0.capabilities, skip_counts)

    # Core's own `setup_network`
    for node, extra_args in zip(nodes, _EXTRA_ARGS, strict=True):
        node.restart(extra_args)
    _connect_all(nodes)
    sync_all(nodes, timeout=_SYNC_TIMEOUT)

    _chains_sync_when_long_enough(nodes)
    _large_reorgs_can_succeed(nodes)
    _peerinfo_includes_headers_presync_height(nodes)
