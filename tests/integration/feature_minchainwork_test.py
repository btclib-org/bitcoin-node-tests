# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_minchainwork`, as bodies over either node.

Read from Core's `test/functional/feature_minchainwork.py`
(`c502b65c007b`, 2026-10-03), an option and the clock beside
node-linking
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
three nodes in a line, each dialling the one before it, the second and
the third under `-minimumchainwork=0x65`
(`Capability.MINIMUM_CHAIN_WORK`) and the third's clock two days ahead
(`Capability.CLOCK`). While the first node's chain (`Capability.MINE`)
has less work than that, no block reaches the third node past the
second: for Core's three seconds its only chain tip is the genesis
block, and for Core's five it answers a peer's `getheaders` with no
header. One block more takes the work past the floor, every node syncs,
and the third node answers the same `getheaders` while its clock keeps
it in initial block download. A `-minimumchainwork` that is not hex
refuses the start in Core's own words.

What differs from Core's file:

- Core's harness starts each node under its own `extra_args`; this
  harness's nodes start without, and the second and the third are
  restarted under the option before they are connected;
- Core's harness starts every node with a `peertimeout` (`write_config`,
  `test_framework/util.py`); here the third node alone is restarted with
  it (`Capability.PEER_TIMEOUT`), the one whose clock moves, so that
  `CConnman::InactivityCheck` (`src/net.cpp`) does not drop its
  connection to the second node once its clock is two days ahead;
- Core's `generate` has the first node mine to the framework's own
  address; here `MiniWallet.generate` (`mini_wallet.py`) builds each
  block client-side and submits it over `submitblock`;
- Core's `ensure_for` over the peer's `last_message` reads what a
  background thread keeps receiving; here the peer's own socket is read
  for the whole window, a `ping` answered on the way;
- Core's last check reads a `last_message["headers"]` the earlier
  request's empty answer already set; here the latest `headers` is
  forgotten before the request is sent again, and the answer has to
  carry a header, the empty answer being what Core's earlier check
  counts as ignored.

A refusal is Core's own `expected_msg`, matched against the whole stderr
of a start that exited with a code other than `0` before its RPC
answered, as `feature_includeconf_test.py` matches one.

Core's last step, `test_outbound_insufficient_work_disconnect`, is a body
of its own, `outbound_peers_with_too_little_work_are_dropped_in_ibd`, so
that a node lacking `Capability.TYPED_OUTBOUND` or
`Capability.DEBUG_LOG` still runs the first. A node started under
`-minimumchainwork=0x1000` is in initial block download with a short chain
of its own, and is sent that chain's headers, which it already holds:
an inbound and a manual peer sending them are kept, with no log line of
the check; an outbound full-relay and a block-relay-only peer sending them
are dropped for "outbound peer headers chain has insufficient work". The
chain is a few blocks mined into the node, not the third node's, and the
manual peer is dialled with `addnode`, where Core's `addconnection` takes
`manual` only on `master`.

`feature_minchainwork_bitcoind_test.py` and
`feature_minchainwork_btclib_node_test.py` run each,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import magic_from_chain
from btclib.block.block_header import BlockHeader
from btclib.p2p import GetHeaders, Headers, Ping, Pong

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import connect_nodes, sync_all
from bitcoin_node_tests.peer import Listener, Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "block_relay_waits_for_the_minimum_chain_work",
    "outbound_peers_with_too_little_work_are_dropped_in_ibd",
]

_MAGIC = magic_from_chain("regtest")

# Core's own `extra_args` for the second and the third node, and the
# work that option names
_MINIMUM_CHAIN_WORK = "-minimumchainwork=0x65"
_NODE_MIN_WORK = 0x65

# Core's own `REGTEST_WORK_PER_BLOCK`, which is the genesis block's work too
_WORK_PER_BLOCK = 2

# how far ahead Core sets the third node's clock, two days
_CLOCK_AHEAD = 48 * 60 * 60

# what Core's `write_config` (`test_framework/util.py`) gives every node
# and the adapters do not: a `peertimeout` under which the moved clock
# drops no peer as inactive
_PEER_TIMEOUT = "-peertimeout=999999999"

# Core's own `ensure_for` durations, in seconds, unscaled as Core's are
_CHAIN_TIPS_WINDOW = 3.0
_HEADERS_WINDOW = 5.0

# Core's own `ensure_for` default `check_interval`
_CHECK_INTERVAL = 0.2

# Core's own `sync_blocks` default timeout
_SYNC_TIMEOUT = 60.0

# Core's own `-minimumchainwork` for the node kept in initial block download
_HIGH_MINIMUM_CHAIN_WORK = "-minimumchainwork=0x1000"

# how many blocks the node's own chain has
_CHAIN_LENGTH = 5

# Core's own line for an outbound peer whose headers carry too little work
_INSUFFICIENT_WORK = "outbound peer headers chain has insufficient work"

# Core's own `expected_msg` for the refused start
_INVALID_WORK = (
    "Error: Invalid minimum work specified (test), must be up to 64 hex digits"
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)


def _ensure_for(duration: float, predicate: Callable[[], bool]) -> None:
    """Core's own `ensure_for`: `predicate` holds for all of `duration`.

    :param duration: how long, in seconds, not scaled.
    :param predicate: checked now, then every `_CHECK_INTERVAL` seconds
        until `duration` has passed.
    """
    end = time.monotonic() + duration
    while True:
        assert predicate(), f"the predicate became false within {duration} s"
        if time.monotonic() > end:
            return
        time.sleep(_CHECK_INTERVAL)


def _no_header_received(peer: Peer) -> bool:
    """Return Core's own predicate: no `headers`, or one carrying none."""
    message = peer.last_message.get("headers")
    return message is None or not Headers.parse(message.payload).headers


def _ensure_no_header_for(peer: Peer, duration: float) -> None:
    """Core's own `ensure_for` over `_no_header_received`, reading the socket.

    Every message the node sends within `duration` is received, so a
    `headers` arriving at any point of the window is seen, and a `ping` is
    answered with its own nonce.

    :param peer: the peer the node answers.
    :param duration: how long, in seconds, not scaled.
    """
    end = time.monotonic() + duration
    while True:
        assert _no_header_received(peer), f"a header arrived within {duration} s"
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        try:
            message = peer.receive(timeout=remaining)
        except TimeoutError:
            continue
        if message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))


def _connected_peer(node: NodeAdapter) -> Peer:
    """Core's own `add_p2p_connection`: a peer past its handshake."""
    peer = Peer(node.p2p_address, _MAGIC)
    try:
        peer.handshake()
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer


def _chain_tips(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `getchaintips`'s own answer."""
    tips = node.rpc.call("getchaintips")
    assert isinstance(tips, list)
    return tips


def _best_block_hash(node: NodeAdapter) -> str:
    """Return `getbestblockhash`'s own answer."""
    block_hash = node.rpc.call("getbestblockhash")
    assert isinstance(block_hash, str)
    return block_hash


def _in_ibd(node: NodeAdapter) -> bool:
    """Return `getblockchaininfo`'s own `initialblockdownload`."""
    info = node.rpc.call("getblockchaininfo")
    assert isinstance(info, dict)
    in_ibd = info["initialblockdownload"]
    assert isinstance(in_ibd, bool)
    return in_ibd


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


def block_relay_waits_for_the_minimum_chain_work(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `setup_network` and `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    nodes = cluster(3)
    node0, node1, node2 = nodes
    for node in nodes:
        require(Capability.MINIMUM_CHAIN_WORK, node.capabilities, skip_counts)
    require(Capability.CLOCK, node2.capabilities, skip_counts)
    require(Capability.PEER_TIMEOUT, node2.capabilities, skip_counts)
    require(Capability.MINE, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node1.capabilities, skip_counts)
    require(Capability.CONNECT, node2.capabilities, skip_counts)

    # node0 <- node1 <- node2, the third node's clock two days ahead
    node1.restart([_MINIMUM_CHAIN_WORK])
    node2.restart([_MINIMUM_CHAIN_WORK, _PEER_TIMEOUT])
    connect_nodes(node1, node0)
    connect_nodes(node2, node1)
    node2.set_mock_time(int(time.time()) + _CLOCK_AHEAD)

    # the most blocks whose work stays below the second node's floor
    starting_blockcount = node2.rpc.call("getblockcount")
    blocks = (_NODE_MIN_WORK - _WORK_PER_BLOCK) // _WORK_PER_BLOCK
    wallet = MiniWallet(node0)
    wallet.generate(blocks)

    # nothing relayed past the second node
    _ensure_for(_CHAIN_TIPS_WINDOW, lambda: len(_chain_tips(node2)) == 1)
    assert _chain_tips(node2)[0]["height"] == 0
    assert _best_block_hash(node1) != _best_block_hash(node0)
    assert node2.rpc.call("getblockcount") == starting_blockcount

    # getheaders to the third node answered with no header
    with _connected_peer(node2) as peer:
        request = GetHeaders(locator=[bytes.fromhex(_best_block_hash(node2))])
        peer.send(request)
        peer.sync_with_ping()
        _ensure_no_header_for(peer, _HEADERS_WINDOW)

        # one block more, past the floor, and every node syncs
        wallet.generate(1)
        sync_all(nodes, timeout=_SYNC_TIMEOUT)

        # the same getheaders answered, the third node still in IBD
        peer.last_message.pop("headers", None)
        peer.send(request)
        peer.sync_with_ping()
        assert not _no_header_received(peer), "no header answered the request"
    assert _in_ibd(node2) is True

    # a -minimumchainwork that is not hex refuses the start
    assert _refused_stderr(node0, ["-minimumchainwork=test"]) == _INVALID_WORK


def _headers_of_the_chain(node: NodeAdapter) -> Headers:
    """Return Core's own `msg_headers` over every block of `node`'s chain."""
    height = node.rpc.call("getblockcount")
    assert isinstance(height, int)
    headers = []
    for at in range(1, height + 1):
        block_hash = node.rpc.call("getblockhash", [at])
        raw = node.rpc.call("getblockheader", [block_hash, False])
        assert isinstance(raw, str)
        headers.append(BlockHeader.parse(bytes.fromhex(raw), check_validity=False))
    return Headers(headers, check_validity=False)


def _dialled_peer(node: NodeAdapter, connection_type: str) -> Peer:
    """Have `node` dial a fresh listener as `connection_type`, and shake hands.

    A `manual` connection is `addnode`'s `onetry`, over v1.
    """
    with Listener(_MAGIC) as listener:
        if connection_type == "manual":
            host, port = listener.address
            node.rpc.call("addnode", [f"{host}:{port}", "onetry", False])
        else:
            node.add_outbound_connection(listener.address, connection_type)
        peer = listener.accept()
    try:
        peer.handshake()
    except BaseException:
        peer.close()
        raise
    return peer


def outbound_peers_with_too_little_work_are_dropped_in_ibd(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `test_outbound_insufficient_work_disconnect`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :raises TypeError: the node declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    (node,) = cluster(1)
    require(Capability.MINIMUM_CHAIN_WORK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.TYPED_OUTBOUND, node.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)

    node.restart([_HIGH_MINIMUM_CHAIN_WORK])
    MiniWallet(node).generate(_CHAIN_LENGTH)
    assert _in_ibd(node) is True
    headers = _headers_of_the_chain(node)

    # inbound and manual peers are kept
    with (
        assert_debug_log(node.debug_log_path, [], [_INSUFFICIENT_WORK], timeout=0),
        Peer(node.p2p_address, _MAGIC) as inbound,
        _dialled_peer(node, "manual") as manual,
    ):
        inbound.handshake()
        for peer in (inbound, manual):
            peer.send(headers)
            peer.sync_with_ping()
            assert peer.is_connected

    # the other two are dropped, each for the line
    for connection_type in ("outbound-full-relay", "block-relay-only"):
        with (
            _dialled_peer(node, connection_type) as peer,
            assert_debug_log(node.debug_log_path, [_INSUFFICIENT_WORK]),
        ):
            peer.send(headers)
            peer.wait_for_disconnect()
