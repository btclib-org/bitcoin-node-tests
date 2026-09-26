# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_eviction`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/p2p_eviction.py` (`1b76e0473647`,
2026-07-24), the option and MiniWallet families together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
once `-maxconnections` leaves no inbound slot for a new peer, bitcoind
evicts an existing inbound one (`Capability.INBOUND_EVICTION`), and never
one of those its eviction logic protects -- here the peers that sent it
a novel block, those that sent it a transaction, and those with the
lowest ping. `MiniWallet` (`Capability.MINE`) funds the transactions and
`build_fork` builds the blocks.

Core's own claim in full: twenty-one inbound peers fill the slots Core's
own arithmetic leaves for transaction-relaying peers, the twenty-second
triggers the eviction, exactly one peer is disconnected, and it is none
of the peers expected to be protected. What fills those slots differs
between builds, and is read from the build (ISS 35): the pinned commit
lets transaction-relaying peers take only half of a node's inbound
slots, where the pinned `31.1` gives every inbound slot to any peer.
`-maxconnections=53` leaves twenty-one transaction-relaying slots under
the split, `-maxconnections=32` twenty-one slots without it, the value
Core's own file carried before `1b76e0473647`, and
`_splits_inbound_slots` below asks the binary's own `-help` which of the
two it is -- `-inboundrelaypercent`, whose default keeps the pinned
commit's half, or the pinned commit's own wording of the split.

`Peer` answers a ping only while a caller is reading, where Core's
`P2PInterface` answers from a background thread, so `_sync_with_ping`
below reads for it: it answers the node's first ping, after Core's own
tenth of a second for a slow peer and at once for a fast one, and it is
the `sync_with_ping` barrier Core's `add_p2p_connection` runs after the
handshake, which returns on the node's own `verack` before the node has
processed this peer's. Core sends a transaction without waiting for it;
this waits for that barrier after it too, so the node has accepted it
before the next peer connects.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
import subprocess
import time
from functools import lru_cache
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Headers, Ping, Pong
from btclib.p2p.data import BlockPayload, TxPayload
from btclib.p2p.magic import magic_from_chain
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, build_fork
from bitcoin_node_tests.node import free_ports
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")

# twenty-one transaction-relaying inbound slots either way: (53 - 11) / 2
# where a node splits its inbound slots by relay, 32 - 11 where it does
# not, eleven being the outbound and feeler slots Core reserves
_MAX_CONNECTIONS_SPLIT = 53
_MAX_CONNECTIONS = 32

# what `-help` prints on a build that splits its inbound slots by relay
# (`src/init.cpp`): from `0bd3d3dfa5` on, the option that sets the share,
# never wrapped; at `1b76e0473647` itself, a clause of `-maxconnections`'s
# own description that `FormatParagraph` may break across lines, matched
# with the output's whitespace collapsed
_SPLIT_OPTION = b"-inboundrelaypercent=<n>"
_SPLIT_HELP = b"percent of the remaining ones can support transaction relay"

# Core's `SlowP2PInterface`: a tenth of a second before each pong
_SLOW = 0.1

# Core's own protection counts: peers that sent a novel block, peers
# that sent a transaction, and peers protected for the lowest ping
_BLOCK_PEERS = 4
_TX_PEERS = 4
_FAST_PEERS = 8
# slow peers, the eviction candidates
_SLOW_PEERS = 5


@lru_cache
def _splits_inbound_slots(executable: str) -> bool:
    """Return whether `executable` splits its inbound slots by relay.

    A probe of the binary, in the standing of `bitcoind.py`'s own
    `_has_wallet`: `-help` names `-inboundrelaypercent`, or states the
    split in `-maxconnections`'s own description, where the build has
    one, and `-nosettings` for the reason `_has_wallet`'s own docstring
    gives.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-help", "-nosettings"], check=True, capture_output=True
    )
    assert b"-maxconnections=<n>" in probe.stdout
    return _SPLIT_OPTION in probe.stdout or _SPLIT_HELP in b" ".join(
        probe.stdout.split()
    )


def _sync_with_ping(
    peer: Peer, *, pong_delay: float, await_node_ping: bool, timeout: float = 30
) -> None:
    """Core's `sync_with_ping`, answering the node's pings on the way.

    `ping(0)` and then a nonzero nonce, and a wait for the `pong` carrying
    that nonce: the node processes a connection's messages in order, so
    that `pong` says everything sent before it has been processed. Every
    `ping` the node sends meanwhile is answered after `pong_delay`; where
    `await_node_ping`, the wait also lasts until one has been, so the node
    has a ping time for this peer before the next one connects.
    """
    nonce = secrets.randbelow(2**64 - 1) + 1
    peer.send(Ping(0))
    peer.send(Ping(nonce))
    synced = False
    pinged = not await_node_ping
    deadline = time.monotonic() + scaled(timeout)
    while not (synced and pinged):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            err_msg = f"no pong for {nonce}, or no ping, within {timeout} s"
            raise TimeoutError(err_msg)
        message = peer.receive(timeout=remaining)
        if message.command == "ping":
            time.sleep(pong_delay)
            peer.send(Pong(Ping.parse(message.payload).nonce))
            pinged = True
        elif message.command == "pong":
            synced = synced or Pong.parse(message.payload).nonce == nonce


def _connect(adapter: BitcoindAdapter, peers: list[Peer], pong_delay: float) -> Peer:
    """Core's `add_p2p_connection`: handshake, then `_sync_with_ping`."""
    peer = Peer(adapter.p2p_address, _MAGIC)
    peers.append(peer)
    peer.handshake()
    _sync_with_ping(peer, pong_delay=pong_delay, await_node_ping=True)
    return peer


def _is_connected(peer: Peer) -> bool:
    """Return whether the node still holds this connection open."""
    try:
        peer.wait_for_disconnect(timeout=0.2)
    except AssertionError:
        return True
    return False


def _wait_until_tip(
    adapter: BitcoindAdapter, block_hash: str, timeout: float = 30
) -> None:
    deadline = time.monotonic() + scaled(timeout)
    while adapter.rpc.call("getbestblockhash") != block_hash:
        if time.monotonic() > deadline:
            err_msg = f"the tip never reached {block_hash} within {timeout} s"
            raise TimeoutError(err_msg)
        time.sleep(0.1)


def _evicted(peers: list[Peer], timeout: float = 30) -> list[int]:
    """Return the indices of the peers the node disconnected, once any is."""
    deadline = time.monotonic() + scaled(timeout)
    while True:
        evicted = [index for index, peer in enumerate(peers) if not _is_connected(peer)]
        if evicted or time.monotonic() > deadline:
            return evicted


def test_the_evicted_inbound_peer_is_never_a_protected_one(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """Core's own `run_test`, one peer after another in Core's own order."""
    require(Capability.INBOUND_EVICTION, BitcoindAdapter.capabilities, skip_counts)
    max_connections = (
        _MAX_CONNECTIONS_SPLIT
        if _splits_inbound_slots(bitcoind_path)
        else _MAX_CONNECTIONS
    )
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-maxconnections={max_connections}",),
    )
    adapter.start()
    peers: list[Peer] = []
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        protected: set[int] = set()

        # protected by sending the node a novel block, the way Core's own
        # `send_blocks_and_test` does: headers, the node's getdata, the block
        for _ in range(_BLOCK_PEERS):
            peer = _connect(adapter, peers, _SLOW)
            block = build_fork(adapter, wallet.script_pub_key, 1)[0]
            peer.send(Headers([block.header]))
            peer.wait_for("getdata")
            peer.send(
                BlockPayload(block, True, check_validity=False), check_validity=False
            )
            _sync_with_ping(peer, pong_delay=_SLOW, await_node_ping=False)
            _wait_until_tip(adapter, block.header.hash.hex())
            protected.add(len(peers) - 1)

        # slow-pinging peers, the eviction candidates
        for _ in range(_SLOW_PEERS):
            _connect(adapter, peers, _SLOW)

        # protected by sending the node a transaction
        for _ in range(_TX_PEERS):
            peer = _connect(adapter, peers, _SLOW)
            tx = wallet.create_self_transfer()
            peer.send(TxPayload(tx, True))
            _sync_with_ping(peer, pong_delay=_SLOW, await_node_ping=False)
            assert tx.id.hex() in adapter.rpc.call("getrawmempool")
            protected.add(len(peers) - 1)

        # protected by the lowest ping: answered at once
        for _ in range(_FAST_PEERS):
            _connect(adapter, peers, 0)

        # the node's own ping times decide which are protected, whichever
        # peer they turn out to be; a peer with none sorts last, as Core's
        # own stand-in value does
        peer_info = sorted(adapter.rpc.call("getpeerinfo"), key=lambda p: p["id"])
        assert len(peer_info) == len(peers)
        pings = sorted(
            range(len(peer_info)),
            key=lambda index: peer_info[index].get("minping", float("inf")),
        )
        protected.update(pings[:_FAST_PEERS])

        # the peer that triggers the eviction
        candidates = list(peers)
        _connect(adapter, peers, _SLOW)
        evicted = _evicted(candidates)
        assert len(evicted) == 1, f"evicted {evicted}"
        assert evicted[0] not in protected, f"evicted {evicted}, protected {protected}"
    finally:
        for peer in peers:
            peer.close()
        adapter.stop()
