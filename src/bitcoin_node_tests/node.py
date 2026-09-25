# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`: how a node starts, stops and restarts, and its RPC.

Step 3 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220):
one base class over what `bitcoind.py` and `btclib_node.py` share --
spawning a process, waiting for its RPC to answer, and tearing it down
again -- with each subclass supplying only what differs: the command
line an option is spelled with, and how RPC authenticates (rule 1 of
that issue names both as the adapter's own).

Reached only over a process and an RPC socket, never in-process: this
module imports no node, `subprocess.Popen` is the whole of how one
starts, and `bitcoin_core_rpc.BitcoinCoreRpcClient` is the whole of how
one answers.
"""

from __future__ import annotations

import socket
import subprocess
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bitcoin_core_rpc import BitcoinCoreRpcClient

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Set as AbstractSet

    from bitcoin_node_tests.capability import Capability

__all__ = [
    "NodeAdapter",
    "connect_nodes",
    "disconnect_nodes",
    "free_port",
    "wait_until_tips_agree",
]

# how long a freshly spawned node is given to answer its first RPC call:
# a regtest node of either kind is up in well under a second on any
# machine that can run this suite, so this bounds the failure case
_STARTUP_TIMEOUT = 30.0


def free_port() -> int:
    """Return a port nothing is listening on, by letting the OS pick one.

    Bound and closed rather than guessed: a fixed port is what makes two
    runs of this suite -- or a node under test and the maintainer's own
    -- fight over one socket.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class _RpcProbe(Protocol):
    """What `_wait_for_rpc` needs of an RPC client: one call, or a raise."""

    def call(self, method: str, params: list[object] | None = None) -> object: ...


class _Process(Protocol):
    """What `_wait_for_rpc` needs of a process: has it already exited."""

    def poll(self) -> int | None: ...


def _wait_for_rpc(
    rpc: _RpcProbe, process: _Process, *, timeout: float = _STARTUP_TIMEOUT
) -> None:
    """Poll `rpc` until it answers, or fail with what the process did instead.

    Shared by both adapters below rather than duplicated: a process
    exiting before its RPC ever answers is failed on that exit code
    rather than left to time out, `bitcoin-core-rpc`'s own transport
    failure -- an empty answer, a refused connection -- being the same
    "not yet listening" either node's own startup answers with.

    :param rpc: the client to poll, one whole call at a time.
    :param process: the process whose own exit ends the wait early.
    :param timeout: how long to wait before giving up.
    :raises TimeoutError: the RPC never answered within `timeout`.
    :raises RuntimeError: the process exited before its RPC answered.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            err_msg = f"node process exited with {exit_code} before its RPC answered"
            raise RuntimeError(err_msg)
        try:
            rpc.call("getblockchaininfo")
        except Exception:  # noqa: BLE001
            # every failure before the node is listening is the same
            # failure: refused, reset, or the cookie/credentials not
            # written yet -- there is nothing to read from any of them
            time.sleep(0.1)
        else:
            return
    err_msg = f"node did not answer its RPC within {timeout} s"
    raise TimeoutError(err_msg)


class NodeAdapter(ABC):
    """One running node: how it starts, stops, restarts, and answers RPC.

    A subclass names its own command line (`_command`), its own RPC
    client (`_rpc_client`) and its own `capabilities`; this class is the
    process and RPC plumbing every node needs regardless -- rule 1's
    "how it starts, stops and restarts" and "how RPC authenticates",
    answered once here and specialised twice.

    `datadir`, `rpc_port` and `p2p_port` are the caller's to allocate --
    `free_port` above, and a fixture's own `tmp_path` -- rather than this
    class reaching for a default any other instance on the same machine
    could collide on.

    `extra_args` is appended after `_command`'s own argv, unexamined by
    this class: a caller asking for a fact `_command` does not already
    name -- a non-default `-blocksdir`, a `-conf` naming a file this
    same caller wrote -- passes it here rather than a subclass growing a
    parameter for every option a test happens to need.
    """

    capabilities: AbstractSet[Capability]

    def __init__(
        self,
        executable: str,
        datadir: Path,
        rpc_port: int,
        p2p_port: int,
        extra_args: Sequence[str] = (),
    ) -> None:
        self._executable = executable
        self._datadir = datadir
        self._rpc_port = rpc_port
        self._p2p_port = p2p_port
        self._extra_args = tuple(extra_args)
        self._process: subprocess.Popen[bytes] | None = None

    @abstractmethod
    def _command(self) -> list[str]:
        """Return the argv this node starts with."""

    @abstractmethod
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a fresh RPC client for this node, however it authenticates."""

    @property
    def p2p_address(self) -> tuple[str, int]:
        """Return `(host, port)` the p2p wire can be dialled at."""
        return ("127.0.0.1", self._p2p_port)

    @property
    def rpc(self) -> BitcoinCoreRpcClient:
        """Return a fresh RPC client for this node.

        Fresh rather than cached: `bitcoin_core_rpc.BitcoinCoreRpcClient`
        holds no connection of its own to go stale across a `restart`,
        and a cached instance built before the cookie file existed would
        be one `stop`/`start` away from reading a credential this node no
        longer recognises.
        """
        return self._rpc_client()

    def start(self) -> None:
        """Spawn the process and wait for its RPC to answer.

        :raises RuntimeError: the process exited before answering.
        :raises TimeoutError: the RPC never answered.
        """
        self._datadir.mkdir(parents=True, exist_ok=True)
        self._process = subprocess.Popen(  # noqa: S603
            [*self._command(), *self._extra_args],
        )
        _wait_for_rpc(self._rpc_client(), self._process, timeout=_STARTUP_TIMEOUT)

    def stop(self) -> None:
        """Terminate the process and wait for it to exit.

        A no-op where nothing was ever started, which is what lets a
        fixture's own teardown call this unconditionally rather than
        track whether `start` succeeded.
        """
        if self._process is None:
            return
        self._process.terminate()
        self._process.wait(timeout=_STARTUP_TIMEOUT)
        self._process = None

    def restart(self) -> None:
        """Stop and start again, over the same data directory.

        The one of the six parts every adapter answers identically: the
        data directory is the caller's, named once in `__init__`, so a
        restart resumes the same chain rather than a fresh one.
        """
        self.stop()
        self.start()


def _peer_ids(peers: object) -> set[object]:
    """Return every `id` a `getpeerinfo` answer carries, or an empty set.

    :param peers: whatever `getpeerinfo` answered.
    """
    if not isinstance(peers, list):
        return set()
    return {peer["id"] for peer in peers if isinstance(peer, dict)}


def _wait_for_peer(
    node: NodeAdapter,
    predicate: Callable[[dict[str, object]], bool],
    deadline: float,
    what: str,
) -> dict[str, object]:
    """Return the first `getpeerinfo` entry of `node` matching `predicate`.

    :param node: the node whose own `getpeerinfo` is polled.
    :param predicate: what the wanted entry looks like.
    :param deadline: a `time.monotonic()` value, not a duration.
    :param what: named in the exception, what this wait was for.
    :raises TimeoutError: no matching entry appeared before `deadline`.
    """
    while time.monotonic() < deadline:
        peers = node.rpc.call("getpeerinfo")
        if isinstance(peers, list):
            for peer in peers:
                if isinstance(peer, dict) and predicate(peer):
                    return peer
        time.sleep(0.1)
    err_msg = f"{node} never reported {what} within the wait"
    raise TimeoutError(err_msg)


def _wait_for_handshake(node: NodeAdapter, peer_id: object, deadline: float) -> None:
    """Wait until `node`'s own peer `peer_id` completed its handshake.

    `GetNodeStats` (`src/net.cpp`), what bitcoind's own `getpeerinfo`
    reads, lists every entry of `m_nodes` regardless of state, a peer
    short of `verack` included -- unlike btclib-node's own answer, whose
    docstring is "one entry per handshake-complete peer", nothing short
    of one ever reaching that list at all. `bytesrecv_per_msg` is
    Core's own field this checks a `pong` of at least 29 bytes against,
    the same wait Core's own `connect_nodes` makes for
    `fSuccessfullyConnected`, since `m_ping_start` starts at the clock's
    own epoch and so the first ping already goes out on the next
    message loop; its absence is read as btclib-node's own guarantee
    already met, rather than as a field to wait for.

    :param node: the node whose own peer is polled.
    :param peer_id: the `id` `getpeerinfo` gave that peer.
    :param deadline: a `time.monotonic()` value, not a duration.
    :raises TimeoutError: the handshake never completed before `deadline`.
    """
    while time.monotonic() < deadline:
        peers = node.rpc.call("getpeerinfo")
        if isinstance(peers, list):
            for peer in peers:
                if not isinstance(peer, dict) or peer.get("id") != peer_id:
                    continue
                counters = peer.get("bytesrecv_per_msg")
                if not isinstance(counters, dict) or counters.get("pong", 0) >= 29:
                    return
                break
        time.sleep(0.1)
    err_msg = f"{node} never completed its own handshake with peer {peer_id!r}"
    raise TimeoutError(err_msg)


def connect_nodes(
    first: NodeAdapter, second: NodeAdapter, *, timeout: float = 30.0
) -> None:
    """Connect `first` to `second`, over `addnode onetry` and `getpeerinfo`.

    Core's own `connect_nodes` (`test/functional/test_framework.py`):
    `addnode ... "onetry"` asks `first` to dial `second`'s own p2p
    address once, immediately. Core then waits for `getpeerinfo` to show
    the connection on *both* sides, matched by subversion, before
    waiting for each side's own `pong` to confirm the handshake is
    actually done; this matches the same three waits, by a criterion
    each side can actually be read off rather than by subversion, since
    this adapter's own nodes carry no per-node subversion tag to tell
    one apart from another. `first`'s own outbound entry is matched by
    address, `second`'s own p2p address being known and unique to it;
    `second`'s own new inbound entry cannot be matched the same way --
    its `addr` is `first`'s ephemeral outbound port, not the address
    `first` itself is reachable at -- so it is matched by an `id` absent
    from a `getpeerinfo` snapshot taken before the dial, the one entry a
    single `connect_nodes` call can have added since (rule 4's "the
    adapter translates a spelling" is why `_wait_for_handshake` reads
    `bytesrecv_per_msg` rather than assuming every adapter answers it:
    btclib-node's own `getpeerinfo` already withholds a peer until its
    handshake is done, so nothing here is adapter-specific except which
    of these waits is a no-op).

    Checking only `first`'s own view is racy under load: `second` can
    take longer to accept and register the same socket than `first`
    takes to see its own outbound half of it, which is what lets
    `sendmsgtopeer` on `second` answer "Could not send message to peer"
    moments after `first` alone would already report the connection.

    :param first: the node asked to dial.
    :param second: the node dialled.
    :param timeout: how long to wait for both sides to report the
        connection and its handshake.
    :raises TimeoutError: either side never reported the connection, or
        its handshake, in time.
    """
    host, port = second.p2p_address
    address = f"{host}:{port}"
    before_second = _peer_ids(second.rpc.call("getpeerinfo"))
    first.rpc.call("addnode", [address, "onetry"])
    deadline = time.monotonic() + timeout

    first_peer = _wait_for_peer(
        first,
        lambda peer: peer.get("addr") == address and not peer.get("inbound"),
        deadline,
        f"a connection to {second}",
    )
    second_peer = _wait_for_peer(
        second,
        lambda peer: bool(peer.get("inbound")) and peer.get("id") not in before_second,
        deadline,
        f"a connection from {first}",
    )
    _wait_for_handshake(first, first_peer["id"], deadline)
    _wait_for_handshake(second, second_peer["id"], deadline)


def disconnect_nodes(
    first: NodeAdapter, second: NodeAdapter, *, timeout: float = 30.0
) -> None:
    """Disconnect `first` from `second`, over `disconnectnode`.

    Core's own `disconnect_nodes`
    (`test/functional/test_framework/test_node.py`): `disconnectnode`
    asks `first` to drop `second`'s own p2p address, and polling
    `getpeerinfo` for that address to disappear is how this waits for the
    drop to land, the same wait `connect_nodes` above makes for a
    connection appearing rather than vanishing.

    Matched against `connect_nodes(first, second)`: `first` is the side
    that dialled, so `second`'s address is what its own outbound entry
    was recorded under, and `disconnectnode`'s address form is what asks
    for exactly that entry rather than one among several a node with
    other peers also carries.

    :param first: the node asked to drop the connection.
    :param second: the node dropped.
    :param timeout: how long to wait for `first` to stop reporting it.
    :raises TimeoutError: `first` still reports the peer after `timeout`.
    """
    host, port = second.p2p_address
    address = f"{host}:{port}"
    first.rpc.call("disconnectnode", [address])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        peers = first.rpc.call("getpeerinfo")
        if isinstance(peers, list) and address not in {peer["addr"] for peer in peers}:
            return
        time.sleep(0.1)
    err_msg = f"{first} still reports a peer at {address} after {timeout} s"
    raise TimeoutError(err_msg)


def wait_until_tips_agree(
    nodes: Sequence[NodeAdapter], *, timeout: float = 30.0
) -> None:
    """Poll every node's `getbestblockhash` until they all agree.

    Core's own `sync_blocks` (`test_framework.py`): propagation over p2p
    relay is asynchronous, so a block one node just mined or received
    reaches the rest of a topology on their own schedule, and this is the
    wait that turns "eventually" into a deadline this suite holds to
    rather than a race the assertion after it would otherwise be.

    :param nodes: the nodes to poll, at least one.
    :param timeout: how long to wait for every hash to match.
    :raises TimeoutError: the nodes never agreed within `timeout`.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        hashes = {node.rpc.call("getbestblockhash") for node in nodes}
        if len(hashes) == 1:
            return
        time.sleep(0.1)
    err_msg = f"nodes did not converge on one tip within {timeout} s"
    raise TimeoutError(err_msg)
