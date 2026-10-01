# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_blockfilters`, one body over either node.

Read from Core's `test/functional/p2p_blockfilters.py` (`3fd68a95e68b`,
2026-04-07), an option and the log beside node-linking
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node under `-blockfilterindex` and `-peerblockfilters`
(`Capability.BLOCK_FILTER_INDEX`, `Capability.PEER_BLOCK_FILTERS`)
signals `NODE_COMPACT_FILTERS` and serves BIP157's `cfcheckpt`,
`cfheaders` and `cfilter` for its active chain and for a stale block
it reorged away from, each matching what `getblockfilter` answers; a
node under `-blockfilterindex` alone does not signal it and drops a
peer asking for any of the three; a request out of range, of an unknown
type or for an unknown block is dropped, each in Core's own words in
the node's log (`Capability.DEBUG_LOG`); and `-peerblockfilters`
without the index, or an unknown index type, refuses the start in
Core's own words.

Core's own claim in full, its chain lengths included: the stale block
and the active chain's tip sit at the heights Core's own ranges need,
the refusal of too many filters and of too many filter headers each
reaching past its own bound. The two nodes share a chain mined by the
first (`Capability.MINE`) while connected (`Capability.CONNECT`), each
then mines apart once disconnected (`Capability.DISCONNECT`), and the
first reorgs onto the second's longer chain once they reconnect.

What differs from Core's file:

- Core's harness connects its nodes at setup; this harness's nodes
  start unconnected, and are connected before the shared chain is mined;
- Core's two peers connect before any block is mined; here they connect
  once the stale block and the longer chain are mined, the peer driven
  by hand reading nothing until it is asked to;
- Core reads `last_message` after each `send_and_ping`, whether or not
  the request drew an answer; here the latest message of the kind is
  forgotten before the request, so an answer left over from an earlier
  request never stands in for a missing one;
- Core's `syncwithvalidationinterfacequeue` is bitcoind's own RPC
  (`src/rpc/blockchain.cpp`), so it is called on bitcoind alone: the
  index learns of a block on events queued behind it
  (`src/validationinterface.cpp`).

A refusal is Core's own `expected_msg`, matched against the whole stderr
of a start that exited with a code other than `0` before its RPC
answered, as `feature_includeconf_test.py` matches one.

`p2p_blockfilters_bitcoind_test.py` and
`p2p_blockfilters_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
import secrets
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import (
    BlockFilterType,
    CFCheckpt,
    CFHeaders,
    CFilter,
    GetCFCheckpt,
    GetCFHeaders,
    GetCFilters,
    Ping,
    Pong,
    ServiceFlags,
)
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import (
    connect_nodes,
    disconnect_nodes,
    wait_until_tips_agree,
)
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from btclib.p2p import Payload

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["TEST_TIMEOUT", "block_filters_are_served_to_peers"]

type _Node = BitcoindAdapter | BtclibNodeAdapter

_MAGIC = magic_from_chain("regtest")

# Core's own `sync_blocks(timeout=600)` over the reorg
_REORG_WAIT = 600.0

# the test's own bound, through `scaled_timeout`: `_REORG_WAIT` is at or
# past `pyproject.toml`'s `timeout`, so the test gets that wait plus the
# ordinary `timeout` for the rest of what it does
TEST_TIMEOUT = _REORG_WAIT + 300.0

# how long the peer waits for each message of a `cfilter` answer
_WAIT = 60.0

# the filter type Core's own request names where no basic filter is
# meant, and the block hash no block has, Core's own `stop_hash` read in
# display order
_UNKNOWN_FILTER_TYPE = 255
_UNKNOWN_BLOCK_HASH = (123456789).to_bytes(32, "big")

# Core's own `expected_msgs`, each a `LogDebug(BCLog::NET, ...)` of
# `PrepareBlockFilterRequest` (`src/net_processing.cpp`)
_UNSUPPORTED = "requested unsupported block filter type"
_TOO_MANY = "requested too many cfilters/cfheaders"
_INVALID_HASH = "requested invalid block hash"
_START_PAST_STOP = (
    "sent invalid getcfilters/getcfheaders with start height 1000 and stop height 999"
)

# Core's own `expected_msg` for each refused start
_WITHOUT_INDEX = "Error: Cannot set -peerblockfilters without -blockfilterindex."
_UNKNOWN_INDEX = "Error: Unknown -blockfilterindex value abc."

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)


def _debug_log(node: _Node, skip_counts: SkipCounts) -> Path:
    """Return the log the refusals are read from, or skip where none is kept.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def _sync_validation_queue(node: NodeAdapter) -> None:
    """Core's own `syncwithvalidationinterfacequeue`, on bitcoind alone."""
    if isinstance(node, BitcoindAdapter):
        node.rpc.call("syncwithvalidationinterfacequeue")


def _block_count(node: NodeAdapter) -> object:
    """Return `getblockcount`'s own answer."""
    return node.rpc.call("getblockcount")


def _block_hash(node: NodeAdapter, height: int) -> str:
    """Return `getblockhash`'s own answer for `height`."""
    block_hash = node.rpc.call("getblockhash", [height])
    assert isinstance(block_hash, str)
    return block_hash


def _filter_header(node: NodeAdapter, block_hash: str) -> bytes:
    """Return `getblockfilter`'s own basic filter header, in display order."""
    result = node.rpc.call("getblockfilter", [block_hash, "basic"])
    assert isinstance(result, dict)
    return bytes.fromhex(result["header"])


def _local_services(node: NodeAdapter) -> int:
    """Return `getnetworkinfo`'s own `localservices`, as an integer."""
    info = node.rpc.call("getnetworkinfo")
    assert isinstance(info, dict)
    return int(info["localservices"], 16)


def _connected_peer(node: NodeAdapter) -> tuple[Peer, int]:
    """Core's own `add_p2p_connection`: a peer past its handshake.

    :returns: the peer, and the services the node's own `version` signals.
    """
    peer = Peer(node.p2p_address, _MAGIC)
    try:
        services = peer.handshake().services
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer, services


def _send_and_ping(peer: Peer, request: Payload, command: str) -> bytes:
    """Core's own `send_and_ping`, then its `last_message[command]`.

    :returns: the payload of the `command` message the request drew.
    """
    peer.last_message.pop(command, None)
    peer.send(request)
    peer.sync_with_ping()
    assert command in peer.last_message, f"no {command!r} answered the request"
    return peer.last_message[command].payload


def _cfilters(peer: Peer, request: GetCFilters) -> list[CFilter]:
    """Core's own `send_and_ping`, then its `FiltersClient.pop_cfilters`.

    Every `cfilter` the node sends ahead of the `pong` answering a `ping`
    sent after the request, in the order sent.
    """
    nonce = secrets.randbelow(2**64 - 1) + 1
    peer.send(request)
    peer.send(Ping(nonce))
    cfilters = []
    while True:
        message = peer.receive(timeout=scaled(_WAIT))
        if message.command == "cfilter":
            cfilters.append(CFilter.parse(message.payload))
        elif message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "pong" and Pong.parse(message.payload).nonce == nonce:
            return cfilters


def _dropped(node: NodeAdapter, log_path: Path, request: Payload, log: str) -> None:
    """Core's own disconnection check: a fresh peer's request, logged, dropped.

    :param node: the node asked.
    :param log_path: its own debug log.
    :param request: the one message the peer sends past its handshake.
    :param log: Core's own `expected_msgs` entry for the refusal.
    """
    peer, _ = _connected_peer(node)
    with peer, assert_debug_log(log_path, [log]):
        peer.send(request)
        peer.wait_for_disconnect()


def _refused_stderr(node: NodeAdapter, extra_args: list[str]) -> str:
    """Start `node` with `extra_args`, and return the stderr it exits with.

    Core's own `assert_start_raises_init_error`: the start fails, with an
    exit code other than `0`, before its RPC ever answers.
    """
    try:
        with pytest.raises(RuntimeError) as refused:
            node.restart(extra_args)
    finally:
        node.stop()
    early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
    assert early_exit is not None
    assert int(early_exit[1]) != 0
    return early_exit[2].strip()


def block_filters_are_served_to_peers(
    cluster: Callable[[int], Sequence[_Node]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    for node in (node0, node1):
        require(Capability.PEER_BLOCK_FILTERS, node.capabilities, skip_counts)
        require(Capability.BLOCK_FILTER_INDEX, node.capabilities, skip_counts)
        require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.DISCONNECT, node0.capabilities, skip_counts)
    log0 = _debug_log(node0, skip_counts)
    log1 = _debug_log(node1, skip_counts)

    # node 0 serves compact filters, node 1 does not
    node0.restart(["-blockfilterindex", "-peerblockfilters"])
    node1.restart(["-blockfilterindex"])

    # the first 999 blocks, shared
    connect_nodes(node0, node1)
    node0.mine(999)
    wait_until_tips_agree([node0, node1])

    # a stale block, mined apart
    disconnect_nodes(node0, node1)
    (stale_block_hash,) = node0.mine(1)
    _sync_validation_queue(node0)
    assert _block_count(node0) == 1000
    node1.mine(1001)
    assert _block_count(node1) == 2000

    peer_0, services_0 = _connected_peer(node0)
    peer_1, services_1 = _connected_peer(node1)
    peer_1.close()
    with peer_0:
        # NODE_COMPACT_FILTERS signalled, and in `localservices`
        assert services_0 & ServiceFlags.NODE_COMPACT_FILTERS
        assert not services_1 & ServiceFlags.NODE_COMPACT_FILTERS
        assert _local_services(node0) & ServiceFlags.NODE_COMPACT_FILTERS
        assert not _local_services(node1) & ServiceFlags.NODE_COMPACT_FILTERS

        # cfcheckpt on the chain about to be reorged out
        stale = bytes.fromhex(stale_block_hash)
        request = GetCFCheckpt(BlockFilterType.BASIC, stale)
        response = CFCheckpt.parse(_send_and_ping(peer_0, request, "cfcheckpt"))
        assert response.filter_type == request.filter_type
        assert response.stop_hash == request.stop_hash
        assert len(response.filter_headers) == 1

        # node 0 reorgs onto node 1's longer chain
        connect_nodes(node0, node1)
        wait_until_tips_agree([node0, node1], timeout=_REORG_WAIT)
        _sync_validation_queue(node0)
        main_block_hash = _block_hash(node0, 1000)
        assert main_block_hash != stale_block_hash, "node 0 did not reorganize"
        main = bytes.fromhex(main_block_hash)

        # cfcheckpt on the active chain
        tip_hash = node0.rpc.call("getbestblockhash")
        assert isinstance(tip_hash, str)
        tip = bytes.fromhex(tip_hash)
        request = GetCFCheckpt(BlockFilterType.BASIC, tip)
        response = CFCheckpt.parse(_send_and_ping(peer_0, request, "cfcheckpt"))
        assert response.filter_type == request.filter_type
        assert response.stop_hash == request.stop_hash
        main_cfcheckpt = _filter_header(node0, main_block_hash)
        tip_cfcheckpt = _filter_header(node0, tip_hash)
        assert response.filter_headers == (main_cfcheckpt, tip_cfcheckpt)

        # cfcheckpt on the stale chain
        request = GetCFCheckpt(BlockFilterType.BASIC, stale)
        response = CFCheckpt.parse(_send_and_ping(peer_0, request, "cfcheckpt"))
        stale_cfcheckpt = _filter_header(node0, stale_block_hash)
        assert response.filter_headers == (stale_cfcheckpt,)

        # cfheaders on the active chain
        cfheaders_request = GetCFHeaders(BlockFilterType.BASIC, 1, main)
        payload = _send_and_ping(peer_0, cfheaders_request, "cfheaders")
        headers = CFHeaders.parse(payload)
        main_cfhashes = headers.filter_hashes
        assert len(main_cfhashes) == 1000
        assert headers.filter_headers[-1] == main_cfcheckpt

        # cfheaders on the stale chain
        cfheaders_request = GetCFHeaders(BlockFilterType.BASIC, 1, stale)
        payload = _send_and_ping(peer_0, cfheaders_request, "cfheaders")
        headers = CFHeaders.parse(payload)
        stale_cfhashes = headers.filter_hashes
        assert len(stale_cfhashes) == 1000
        assert headers.filter_headers[-1] == stale_cfcheckpt

        # cfilters on the active chain, each hashing to its cfheaders entry
        stop_hash = bytes.fromhex(_block_hash(node0, 10))
        cfilters = _cfilters(peer_0, GetCFilters(BlockFilterType.BASIC, 1, stop_hash))
        assert len(cfilters) == 10
        for cfilter, cfhash, height in zip(
            cfilters, main_cfhashes, range(1, 11), strict=False
        ):
            assert cfilter.filter_type == BlockFilterType.BASIC
            assert cfilter.block_hash == bytes.fromhex(_block_hash(node0, height))
            assert cfilter.basic_filter.hash == cfhash

        # cfilters for the stale block
        cfilters = _cfilters(peer_0, GetCFilters(BlockFilterType.BASIC, 1000, stale))
        assert len(cfilters) == 1
        (cfilter,) = cfilters
        assert cfilter.filter_type == BlockFilterType.BASIC
        assert cfilter.block_hash == stale
        assert cfilter.basic_filter.hash == stale_cfhashes[999]

    # node 1, without NODE_COMPACT_FILTERS, drops each request
    unsupported: tuple[Payload, ...] = (
        GetCFCheckpt(BlockFilterType.BASIC, main),
        GetCFHeaders(BlockFilterType.BASIC, 1000, main),
        GetCFilters(BlockFilterType.BASIC, 1000, main),
    )
    for unsupported_request in unsupported:
        _dropped(node1, log1, unsupported_request, _UNSUPPORTED)

    # node 0 drops each invalid request
    below_main = bytes.fromhex(_block_hash(node0, 999))
    invalid: tuple[tuple[Payload, str], ...] = (
        (GetCFilters(BlockFilterType.BASIC, 0, main), _TOO_MANY),
        (GetCFHeaders(BlockFilterType.BASIC, 0, tip), _TOO_MANY),
        (GetCFCheckpt(_UNKNOWN_FILTER_TYPE, main), _UNSUPPORTED),
        (GetCFCheckpt(BlockFilterType.BASIC, _UNKNOWN_BLOCK_HASH), _INVALID_HASH),
        (GetCFHeaders(BlockFilterType.BASIC, 1000, below_main), _START_PAST_STOP),
    )
    for invalid_request, log in invalid:
        _dropped(node0, log0, invalid_request, log)

    # -peerblockfilters without -blockfilterindex, and an unknown index type
    assert _refused_stderr(node0, ["-peerblockfilters"]) == _WITHOUT_INDEX
    assert _refused_stderr(node0, ["-blockfilterindex=abc"]) == _UNKNOWN_INDEX
