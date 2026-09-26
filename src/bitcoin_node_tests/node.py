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
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from urllib.request import Request

from bitcoin_core_rpc import BitcoinCoreRpcClient
from bitcoin_core_rpc.transport import HttpTransport

from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Set as AbstractSet

    from bitcoin_node_tests.capability import Capability

__all__ = [
    "NodeAdapter",
    "connect_nodes",
    "disconnect_nodes",
    "free_port",
    "free_ports",
    "sync_all",
    "traced_transport",
    "wait_until_disconnected",
    "wait_until_mempools_agree",
    "wait_until_tips_agree",
]

# how long a freshly spawned node is given to answer its first RPC call:
# a regtest node of either kind is up in well under a second on any
# machine that can run this suite, so this bounds the failure case
_STARTUP_TIMEOUT = 30.0

# where `start` redirects a node's own stderr, inside its datadir, and
# where `start` and `stop` each read it back into the error they raise
_STDERR_LOG = "node-stderr.log"

# the exit code `stop` accepts, for every adapter: Core's own
# `TestNode.stop_node` expects 0, and each node exits 0 on `terminate`'s
# SIGTERM -- measured on bitcoind 31.1, btclib-node 2026.9.24 and
# btclib-node's `main` at f8f7143
_CLEAN_EXIT = 0


def free_port() -> int:
    """Return a port nothing is listening on, by letting the OS pick one.

    Bound and closed rather than guessed: a fixed port is what makes two
    runs of this suite -- or a node under test and the maintainer's own
    -- fight over one socket. Core's own `p2p_port`/`rpc_port`
    (`test_framework/util.py`) take the opposite trade, a formula over a
    per-process `PortSeed` and a node index rather than a port the OS
    ever confirmed was free: that avoids two of Core's own ports
    colliding at all, at the cost of a seed some caller has to keep
    unique, which this suite has nothing to hold one in -- `pytest-xdist`
    workers here share no counterpart to Core's one seed per test
    process.

    A single call answers for one port. Two calls in a row have nothing
    telling them apart: each binds, reads its own port back and closes
    before the next one opens, so the second can be handed the very port
    the first just freed. `free_ports` below is what a caller after more
    than one port at once wants instead.
    """
    return free_ports(1)[0]


def free_ports(count: int) -> tuple[int, ...]:
    """Return `count` ports nothing is listening on, pairwise distinct.

    Every probe socket stays open until all `count` are bound, so the OS
    -- which never hands out the port of a socket that is still open --
    cannot repeat one of them the way `count` separate calls of
    `free_port` above can: each of those closes its own probe, and so
    frees its port again, before the next one ever binds.

    :param count: how many ports to return.
    """
    with ExitStack() as probes:
        sockets = [probes.enter_context(socket.socket()) for _ in range(count)]
        for probe in sockets:
            probe.bind(("127.0.0.1", 0))
        return tuple(int(probe.getsockname()[1]) for probe in sockets)


def traced_transport(transport: HttpTransport) -> HttpTransport:
    """Wrap `transport`, printing every RPC exchange it carries.

    Core's own `--tracerpc` (`test_framework.py`): "Print out all RPC
    calls as they are made". `bitcoin_core_rpc.BitcoinCoreRpcClient`'s
    own `transport=` is exactly the two-argument callable
    (`bitcoin_core_rpc.transport.HttpTransport`) this wraps, an
    already-built `Request` and a timeout answered with a status and a
    body, so tracing needs no change to the client itself.

    :param transport: the transport to wrap, `urlopen_transport`
        (`bitcoin_core_rpc.transport`) unless a caller already passed
        something else.
    """

    def _traced(request: Request, timeout: float) -> tuple[int, bytes]:
        print(f"--> {request.full_url} {request.data!r}")  # noqa: T201
        status, body = transport(request, timeout)
        print(f"<-- {status} {body!r}")  # noqa: T201
        return status, body

    return _traced


class _RpcProbe(Protocol):
    """What `_wait_for_rpc` needs of an RPC client: one call, or a raise."""

    def call(self, method: str, params: list[object] | None = None) -> object: ...


class _Process(Protocol):
    """What `_wait_for_rpc` needs of a process: has it already exited."""

    def poll(self) -> int | None: ...


def _option_name(token: str) -> str | None:
    """Return the bare option name `token` spells, or `None` if it spells none.

    `-opt`, `--opt`, `-opt=value` and `--opt=value` all name `opt`; a
    token carrying no leading dash -- an executable path, a bare
    positional -- names nothing, and neither does a lone `-`.

    :param token: one argv entry.
    """
    if not token.startswith("-"):
        return None
    name = token.lstrip("-").split("=", 1)[0]
    return name or None


def _canonical_option_name(name: str) -> str:
    """Collapse Core's own negated spelling onto the option it negates.

    bitcoind treats `-noopt` as `-opt=0`
    (`ArgsManager::GetBoolArg`, `src/util/args.cpp`), so `noopt` and
    `opt` name the same knob and compare equal here.

    :param name: an option name, as `_option_name` returns it.
    """
    if name.startswith("no") and len(name) > len("no"):
        return name[len("no") :]
    return name


def _reserved_option_names(command: Sequence[str]) -> frozenset[str]:
    """Return every option name `command` itself sets, canonicalized.

    Read out of the adapter's own `_command()` rather than kept by hand
    beside it: an argument `_command` grows is reserved from the commit
    that adds it, with nothing else to update.

    :param command: an adapter's own argv, `_command()`'s answer.
    """
    names = (_option_name(token) for token in command)
    return frozenset(_canonical_option_name(name) for name in names if name is not None)


def _check_extra_args(command: Sequence[str], extra_args: Sequence[str]) -> None:
    """Refuse an `extra_args` entry naming an option `command` already sets.

    bitcoind takes the last of a repeated option with no diagnostic
    (measured against the pinned 31.1, given `-datadir` twice), so an
    `extra_args` entry that names one of `command`'s own options
    replaces it silently once appended after `command` -- refused here
    instead, before either ever reaches a process.

    :param command: the adapter's own argv, `_command()`'s answer.
    :param extra_args: what a caller asks to append after it.
    :raises ValueError: an entry of `extra_args` names an option
        `command` already sets, spelled with one or two leading dashes,
        with or without a `-no` negation.
    """
    reserved = _reserved_option_names(command)
    for arg in extra_args:
        name = _option_name(arg)
        if name is None:
            continue
        canonical = _canonical_option_name(name)
        if canonical in reserved:
            err_msg = f"extra_args reuses -{canonical}, which this adapter sets itself"
            raise ValueError(err_msg)


def _read_stderr(stderr_path: Path) -> str:
    """Return what a node wrote to `stderr_path`, for the error raised on it.

    :param stderr_path: where `start` redirected the node's own stderr.
    """
    return stderr_path.read_bytes().decode("utf-8", errors="replace").strip()


def _wait_for_rpc(
    rpc: _RpcProbe,
    process: _Process,
    stderr_path: Path,
    *,
    timeout: float = _STARTUP_TIMEOUT,
) -> None:
    """Poll `rpc` until it answers, or fail with what the process did instead.

    Shared by both adapters below rather than duplicated: a process
    exiting before its RPC ever answers is failed on that exit code
    rather than left to time out, `bitcoin-core-rpc`'s own transport
    failure -- an empty answer, a refused connection -- being the same
    "not yet listening" either node's own startup answers with.

    :param rpc: the client to poll, one whole call at a time.
    :param process: the process whose own exit ends the wait early.
    :param stderr_path: where the process's own stderr was redirected;
        read back into the error raised on an early exit.
    :param timeout: how long to wait before giving up.
    :raises TimeoutError: the RPC never answered within `timeout`.
    :raises RuntimeError: the process exited before its RPC answered.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            err_msg = (
                f"node process exited with {exit_code} before its RPC "
                f"answered -- stderr: {_read_stderr(stderr_path)}"
            )
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

    `extra_args` is appended after `_command`'s own argv: a caller
    asking for a fact `_command` does not already name -- a non-default
    `-blocksdir`, a `-conf` naming a file this same caller wrote --
    passes it here rather than a subclass growing a parameter for every
    option a test happens to need. An entry naming an option `_command`
    already sets is refused at construction, and in the replacement
    `restart` takes, rather than silently overriding it the way
    bitcoind's own last-one-wins parsing would.

    `rpc_auth` is the credential a subclass's own `_rpc_client` builds
    its readiness and its ordinary RPC client from instead of its own
    default (a cookie, `BitcoindAdapter`'s and, where the build writes
    one, `BtclibNodeAdapter`'s): a node started with `-rpcuser`/
    `-rpcpassword` or `-norpccookiefile` writes no cookie at all
    ([ISS bitcoin-node-tests#34](https://github.com/btclib-org/bitcoin-node-tests/issues/34)),
    so a client waiting on one never sees it and `start` times out
    rather than the node ever answering. The caller who put such a flag
    in `extra_args` already knows the plaintext credential it configured
    -- Core's own `rpc_users.py` builds its own `-rpcauth` lines the same
    way, `rpcauth.py`'s own hash of a password it also keeps -- so it is
    the caller's to pass here too, rather than something this class
    could derive from the command line after the fact: a `-rpcauth`
    value is a salted hash, and the plaintext behind it exists only where
    it was chosen.

    `trace_rpc` is Core's own `--tracerpc`, restated per adapter rather
    than as a global: a subclass's own `_rpc_client` reads
    `self._trace_rpc` and wraps the transport it builds with
    `traced_transport` where it is set, wrapping whichever client that
    method already builds -- `rpc_auth`'s credential one included --
    rather than this base class building the client itself.
    """

    capabilities: AbstractSet[Capability]

    def __init__(
        self,
        executable: str,
        datadir: Path,
        rpc_port: int,
        p2p_port: int,
        extra_args: Sequence[str] = (),
        rpc_auth: tuple[str, str] | None = None,
        *,
        trace_rpc: bool = False,
    ) -> None:
        self._executable = executable
        self._datadir = datadir
        self._rpc_port = rpc_port
        self._p2p_port = p2p_port
        _check_extra_args(self._command(), extra_args)
        self._extra_args = tuple(extra_args)
        self._rpc_auth = rpc_auth
        self._trace_rpc = trace_rpc
        self._process: subprocess.Popen[bytes] | None = None

    @abstractmethod
    def _command(self) -> list[str]:
        """Return the argv this node starts with."""

    @abstractmethod
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a fresh RPC client for this node, however it authenticates.

        `self._trace_rpc` is what a subclass's own implementation wraps
        the transport it builds with, through `traced_transport`.
        """

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

        The process's own stderr is captured into a file under `datadir`
        rather than an unread `subprocess.PIPE`: a pipe nobody drains
        fills its kernel buffer once a long-running node writes past it,
        and then blocks the node on every write past that, where a file
        never blocks the writer regardless of how much it writes.

        A start that raises leaves nothing running: the process is killed
        and forgotten before the error propagates, the way Core's own
        `TestNode.assert_start_raises_init_error` ends one, so a caller's
        own teardown has no process to lose track of and `stop` stays a
        no-op after it
        ([ISS 79](https://github.com/btclib-org/bitcoin-node-tests/issues/79)).

        A process this adapter already holds is refused rather than
        replaced: the replaced one would keep running past `stop`, holding
        its datadir's lock and its ports
        ([ISS 92](https://github.com/btclib-org/bitcoin-node-tests/issues/92)).
        Core's own `TestNode.assert_start_raises_init_error` asserts the
        same of its node before spawning one.

        :raises RuntimeError: this adapter already holds a process, which
            `stop` ends; or the process exited before answering, the
            message carrying what it wrote to stderr.
        :raises TimeoutError: the RPC never answered.
        """
        if self._process is not None:
            err_msg = "node already started: stop it before starting it again"
            raise RuntimeError(err_msg)
        self._start(self._extra_args)

    def _start(self, extra_args: tuple[str, ...]) -> None:
        """Do what `start` documents, appending `extra_args` to `_command`.

        :param extra_args: already checked against `_command`, by
            `__init__` or by `restart`.
        """
        self._datadir.mkdir(parents=True, exist_ok=True)
        stderr_path = self._datadir / _STDERR_LOG
        with stderr_path.open("wb") as stderr_file:
            self._process = subprocess.Popen(  # noqa: S603
                [*self._command(), *extra_args],
                stderr=stderr_file,
            )
        try:
            _wait_for_rpc(
                self._rpc_client(),
                self._process,
                stderr_path,
                timeout=scaled(_STARTUP_TIMEOUT),
            )
        except BaseException:
            process, self._process = self._process, None
            process.kill()
            process.wait(timeout=scaled(_STARTUP_TIMEOUT))
            raise

    def stop(self) -> None:
        """Terminate the process, wait for it to exit, and read how it did.

        A no-op where nothing was ever started, which is what lets a
        fixture's own teardown call this unconditionally rather than
        track whether `start` succeeded.

        A process still running once the wait expires is killed rather
        than left behind holding its datadir and ports, then waited for
        over the same bound, the way Core's own `TestNode.kill_process`
        ends one; the slow shutdown is then raised, not hidden
        ([ISS 76](https://github.com/btclib-org/bitcoin-node-tests/issues/76)).

        An exit code other than `_CLEAN_EXIT` is raised too, whether the
        process had already exited before this call -- a crash during the
        test, which a test's own last RPC call would not have seen -- or
        exited so on `terminate`: Core's own `TestNode.stop_node` checks
        the code the same way
        ([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)).
        A process that had already exited with `_CLEAN_EXIT`, the way an
        RPC `stop` ends one, is a clean stop.

        Stderr is carried in the error and does not fail a clean exit on
        its own, unlike Core's `expected_stderr=''`: `_STDERR_LOG` is one
        file per datadir, so a second process refused over the same
        datadir writes its init error into the log of a node that then
        stops cleanly, as `feature_filelock_bitcoind_test.py`'s second
        process does.

        Each of these raises only once the process has exited and been
        forgotten, so nothing is left running and a second `stop` is a
        no-op.

        :raises TimeoutError: the process ignored the termination for the
            whole wait and was killed; the message carries what it wrote
            to stderr.
        :raises RuntimeError: the process exited with a code other than
            `_CLEAN_EXIT`; the message carries the code, whether it had
            already exited before this call, and what it wrote to stderr.
        """
        if self._process is None:
            return
        process, self._process = self._process, None
        already_exited = process.poll() is not None
        process.terminate()
        timeout = scaled(_STARTUP_TIMEOUT)
        stderr_path = self._datadir / _STDERR_LOG
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=timeout)
            err_msg = (
                f"node process ignored terminate for {timeout}s and was "
                f"killed -- stderr: {_read_stderr(stderr_path)}"
            )
            raise TimeoutError(err_msg) from None
        if exit_code != _CLEAN_EXIT:
            when = "before stop was called" if already_exited else "on terminate"
            err_msg = (
                f"node process exited with {exit_code} {when} -- "
                f"stderr: {_read_stderr(stderr_path)}"
            )
            raise RuntimeError(err_msg)

    def restart(self, extra_args: Sequence[str] | None = None) -> None:
        """Stop and start again, over the same data directory.

        The one of the six parts every adapter answers identically: the
        data directory is the caller's, named once in `__init__`, so a
        restart resumes the same chain rather than a fresh one.

        `extra_args`, where given, replaces the constructor's own for this
        start alone, and a later `start` or `restart` without it goes back
        to the constructor's: Core's own `restart_node(i, extra_args)`
        (`test_framework.py`), whose `TestNode.start` falls back to the
        node's own `extra_args` wherever none is passed. An empty sequence
        is a start with no extra argument at all.

        :param extra_args: what to append after `_command`'s own argv for
            this start, in place of the constructor's.
        :raises ValueError: an entry of `extra_args` names an option
            `_command` already sets, refused the way `__init__` refuses
            one and before the running node is stopped.
        """
        if extra_args is None:
            args = self._extra_args
        else:
            _check_extra_args(self._command(), extra_args)
            args = tuple(extra_args)
        self.stop()
        self._start(args)

    def set_mock_time(self, timestamp: int) -> None:
        """Set this node's own clock, over `setmocktime`.

        Core's own `TestNode.setmocktime`
        (`test/functional/test_framework/test_node.py`) wraps the same
        RPC; `Capability.CLOCK` (`capability.py`) is what a caller checks
        before calling this, a node not declaring it having no
        `setmocktime` to wrap.

        :param timestamp: the unix time this node's own clock reads from
            now on; `0` releases it back to the wall clock.
        """
        self.rpc.call("setmocktime", [timestamp])


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
    first: NodeAdapter,
    second: NodeAdapter,
    *,
    timeout: float = 30.0,
    v2transport: bool = False,
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

    `addnode`'s own third argument, `v2transport`, is passed explicitly,
    `False` unless the caller asks otherwise, rather than left to
    `first`'s own default: bitcoind's own default is
    `True` since the pinned `31.1` (measured live -- a bare `addnode
    ... "onetry"` against a `BtclibNodeAdapter` never completes a
    handshake, bitcoind's own `debug.log` reading "start sending v2
    handshake to peer=0" immediately followed by "socket closed,
    disconnecting peer=0"), and no adapter this repository builds speaks
    BIP324 -- `peer.py`'s own module docstring already states this
    suite's own wire is v1 only, and `btclib-node`'s own `add_node`
    reads and type-checks the argument without ever acting on it
    (`rpc/callbacks.py`'s own docstring). bitcoind itself never falls
    back to v1 once a v2 attempt is reset
    ([ISS btclib-node#1197](https://github.com/btclib-org/btclib-node/issues/1197)),
    which is why it is stated rather than left to a fallback. Core's own
    `connect_nodes` (`test_framework.py`) makes the identical choice
    through its own `peer_advertises_v2` parameter, defaulting to
    whichever side is dialling; here the default is v1, the one wire
    every adapter speaks, and a test whose subject is BIP324 between two
    nodes declaring `Capability.V2TRANSPORT` passes `v2transport=True`.

    :param first: the node asked to dial.
    :param second: the node dialled.
    :param timeout: how long to wait for both sides to report the
        connection and its handshake, before `--timeout-factor`'s own
        scaling (`timeout_factor.scaled`).
    :param v2transport: `addnode`'s own `v2transport` argument, whether
        `first` dials over BIP324.
    :raises TimeoutError: either side never reported the connection, or
        its handshake, in time.
    """
    timeout = scaled(timeout)
    host, port = second.p2p_address
    address = f"{host}:{port}"
    before_second = _peer_ids(second.rpc.call("getpeerinfo"))
    first.rpc.call("addnode", [address, "onetry", v2transport])
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


def wait_until_disconnected(
    node: NodeAdapter, peer: NodeAdapter, *, timeout: float = 30.0
) -> None:
    """Wait until `node`'s own `getpeerinfo` no longer names `peer`'s address.

    Core's own `is_connected_to`
    (`test/functional/test_framework/test_node.py`) is `self.wait_until`
    wrapped around it, matched by `getnetworkinfo`'s own subversion
    string; this matches by p2p address instead, for the same reason
    `connect_nodes` above does -- this adapter's own nodes carry no
    per-node subversion tag. So `node` is the side that dialled: its
    outbound entry carries `peer`'s own listening address, where `peer`'s
    inbound entry for `node` carries an ephemeral port no `p2p_address`
    names, and a call with the two swapped returns at once.

    Unlike `disconnect_nodes` below, this makes no RPC call of its own:
    the drop it waits for is triggered some other way -- `rpc_setban`'s
    own subject, a `setban` on `peer`'s own side dropping the connection
    it matches -- and `disconnect_nodes` is `first.rpc.call
    ("disconnectnode", ...)` followed by exactly this wait, `first` for
    `node` and `second` for `peer`.

    :param node: the node whose own `getpeerinfo` is polled.
    :param peer: the peer whose address must disappear from it.
    :param timeout: how long to wait, before `--timeout-factor`'s own
        scaling.
    :raises TimeoutError: `node` still reports `peer` after `timeout`.
    """
    timeout = scaled(timeout)
    host, port = peer.p2p_address
    address = f"{host}:{port}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        peers = node.rpc.call("getpeerinfo")
        if isinstance(peers, list) and address not in {p["addr"] for p in peers}:
            return
        time.sleep(0.1)
    err_msg = f"{node} still reports a peer at {address} after {timeout} s"
    raise TimeoutError(err_msg)


def disconnect_nodes(
    first: NodeAdapter, second: NodeAdapter, *, timeout: float = 30.0
) -> None:
    """Disconnect `first` from `second`, over `disconnectnode`.

    Core's own `disconnect_nodes`
    (`test/functional/test_framework/test_node.py`): `disconnectnode`
    asks `first` to drop `second`'s own p2p address, and
    `wait_until_disconnected` above is how this waits for the drop to
    land, the same wait `connect_nodes` above makes for a connection
    appearing rather than vanishing.

    Matched against `connect_nodes(first, second)`: `first` is the side
    that dialled, so `second`'s address is what its own outbound entry
    was recorded under, and `disconnectnode`'s address form is what asks
    for exactly that entry rather than one among several a node with
    other peers also carries.

    :param first: the node asked to drop the connection.
    :param second: the node dropped.
    :param timeout: how long to wait for `first` to stop reporting it,
        before `--timeout-factor`'s own scaling.
    :raises TimeoutError: `first` still reports the peer after `timeout`.
    """
    host, port = second.p2p_address
    address = f"{host}:{port}"
    first.rpc.call("disconnectnode", [address])
    wait_until_disconnected(first, second, timeout=timeout)


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
    :param timeout: how long to wait for every hash to match, before
        `--timeout-factor`'s own scaling.
    :raises TimeoutError: the nodes never agreed within `timeout`.
    """
    timeout = scaled(timeout)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        hashes = {node.rpc.call("getbestblockhash") for node in nodes}
        if len(hashes) == 1:
            return
        time.sleep(0.1)
    err_msg = f"nodes did not converge on one tip within {timeout} s"
    raise TimeoutError(err_msg)


def wait_until_mempools_agree(
    nodes: Sequence[NodeAdapter], *, timeout: float = 30.0
) -> None:
    """Poll every node's `getrawmempool` until they all hold the same set.

    Core's own `sync_mempools` (`test_framework.py`): a transaction
    relayed over p2p reaches every node in a topology on its own
    schedule, exactly as a block does, which is `wait_until_tips_agree`
    above's own reason restated for the mempool rather than the chain.
    Core's own version also calls `syncwithvalidationinterfacequeue` on
    every node once they agree, flushing a background validation queue
    bitcoind's own tests care about; this drops it; it is a call this
    adapter's own node has no equivalent of, and no capability declares.

    :param nodes: the nodes to poll, at least one.
    :param timeout: how long to wait for every mempool to match, before
        `--timeout-factor`'s own scaling.
    :raises TimeoutError: the nodes never agreed within `timeout`.
    """
    timeout = scaled(timeout)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pools = {frozenset(node.rpc.call("getrawmempool")) for node in nodes}
        if len(pools) == 1:
            return
        time.sleep(0.1)
    err_msg = f"nodes did not converge on one mempool within {timeout} s"
    raise TimeoutError(err_msg)


def sync_all(nodes: Sequence[NodeAdapter], *, timeout: float = 30.0) -> None:
    """Wait for every node's tip, then every node's mempool, to agree.

    Core's own `sync_all` (`test_framework.py`): `wait_until_tips_agree`
    first, since a mempool's own transactions are commonly what a block
    just mined is meant to clear -- checking the mempool first could
    observe an old one, on a node whose new tip has not landed yet.

    :param nodes: the nodes to wait on, at least one.
    :param timeout: forwarded to each of the two waits in turn, each
        scaling it by `--timeout-factor`, so the call bounds at twice the
        scaled value rather than once.
    """
    wait_until_tips_agree(nodes, timeout=timeout)
    wait_until_mempools_agree(nodes, timeout=timeout)
