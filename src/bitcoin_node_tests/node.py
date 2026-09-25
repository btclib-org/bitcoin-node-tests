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
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from bitcoin_core_rpc import BitcoinCoreRpcClient

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from bitcoin_node_tests.capability import Capability

__all__ = [
    "NodeAdapter",
    "connect_nodes",
    "free_port",
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
    """

    capabilities: AbstractSet[Capability]

    def __init__(
        self, executable: str, datadir: Path, rpc_port: int, p2p_port: int
    ) -> None:
        self._executable = executable
        self._datadir = datadir
        self._rpc_port = rpc_port
        self._p2p_port = p2p_port
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
            self._command(),
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


def connect_nodes(
    first: NodeAdapter, second: NodeAdapter, *, timeout: float = 30.0
) -> None:
    """Connect `first` to `second`, over `addnode` and `getnetworkinfo`.

    Core's own `connect_nodes`
    (`test/functional/test_framework/test_node.py`): `addnode` asks
    `first` to dial `second`'s own p2p address, and polling
    `getnetworkinfo`'s `connections` is how this waits for the dial to
    land rather than assuming a fixed delay -- the same wait Core's own
    helper makes, over the RPC both adapters already answer identically
    (rule 4's "the adapter translates a spelling" has nothing to do here
    yet, both nodes naming this one call the same way; a third node
    spelling it otherwise is what would give this function a second
    branch).

    :param first: the node asked to dial.
    :param second: the node dialled.
    :param timeout: how long to wait for `first` to report the connection.
    :raises TimeoutError: `first` never reported the connection.
    """
    host, port = second.p2p_address
    first.rpc.call("addnode", [f"{host}:{port}", "add"])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        info = first.rpc.call("getnetworkinfo")
        if isinstance(info, dict) and info.get("connections", 0) > 0:
            return
        time.sleep(0.1)
    err_msg = f"{first} never reported a connection to {second} within {timeout} s"
    raise TimeoutError(err_msg)
