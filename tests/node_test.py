# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own process and RPC plumbing, faked rather than spawned.

`_wait_for_rpc` is what makes a node's `start` non-trivial to get
covered honestly: it polls an RPC client and reads a process's own exit
code, neither of which needs a real node to exercise -- a fake of each,
matching the `Protocol`s `node.py` declares for them, drives every
branch.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override
from unittest.mock import ANY, MagicMock, patch

import pytest

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter, connect_nodes, free_port

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet


class _FakeRpc:
    """A `bitcoin_core_rpc.BitcoinCoreRpcClient` stand-in: answers, or raises.

    `answers_after` is how many calls fail (a connection refused, in
    substance) before the next one succeeds -- `0` for a node that is up
    immediately, matching what `node_test.py`'s own callers ask for.
    """

    def __init__(self, answers_after: int = 0) -> None:
        self._remaining = answers_after
        self.calls: list[tuple[str, list[object] | None]] = []

    def call(self, method: str, params: list[object] | None = None) -> object:
        self.calls.append((method, params))
        if self._remaining > 0:
            self._remaining -= 1
            err_msg = "connection refused"
            raise ConnectionRefusedError(err_msg)
        return {"chain": "regtest"}


class _FakeProcess:
    """A `subprocess.Popen` stand-in: `poll` answers `None` until it exits."""

    def __init__(self, exit_after: int | None = None) -> None:
        self._polls = 0
        self._exit_after = exit_after

    def poll(self) -> int | None:
        self._polls += 1
        if self._exit_after is not None and self._polls > self._exit_after:
            return 1
        return None


class _FakeAdapter(NodeAdapter):
    """The smallest concrete `NodeAdapter`: a fake command and a fake client."""

    capabilities: AbstractSet[Capability] = frozenset()

    def __init__(self, *args: object, rpc: _FakeRpc, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._rpc = rpc

    @override
    def _command(self) -> list[str]:
        return ["fake-node", f"-datadir={self._datadir}"]

    @override
    def _rpc_client(self) -> _FakeRpc:  # type: ignore[override]
        return self._rpc


def test_free_port_returns_a_bindable_port() -> None:
    """The port `free_port` returns is free to bind at the moment it answers."""
    import socket  # noqa: PLC0415

    port = free_port()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))


def test_start_waits_for_the_rpc_and_creates_the_datadir(tmp_path: Path) -> None:
    """`start` creates the data directory and blocks until the RPC answers."""
    datadir = tmp_path / "node"
    rpc = _FakeRpc(answers_after=2)
    adapter = _FakeAdapter("fake-node", datadir, 0, 0, rpc=rpc)
    with patch("subprocess.Popen", return_value=_FakeProcess()) as popen:
        adapter.start()
    popen.assert_called_once_with(["fake-node", f"-datadir={datadir}"])
    assert datadir.is_dir()
    assert rpc.calls == [("getblockchaininfo", None)] * 3


def test_start_raises_if_the_process_exits_first(tmp_path: Path) -> None:
    """A process gone before its RPC answers is a `RuntimeError`, not a hang."""
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with (
        patch("subprocess.Popen", return_value=_FakeProcess(exit_after=0)),
        pytest.raises(RuntimeError, match="exited with 1"),
    ):
        adapter.start()


def test_start_raises_on_a_timeout(tmp_path: Path) -> None:
    """An RPC that never answers within the deadline is a `TimeoutError`."""
    from bitcoin_node_tests import node as node_module  # noqa: PLC0415

    adapter = _FakeAdapter(
        "fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc(answers_after=10**6)
    )
    with (
        patch("subprocess.Popen", return_value=_FakeProcess()),
        patch.object(node_module, "_STARTUP_TIMEOUT", 0.0),
        pytest.raises(TimeoutError, match="did not answer"),
    ):
        adapter.start()


def test_stop_is_a_no_op_before_start(tmp_path: Path) -> None:
    """`stop` before `start` is a no-op, not a raise on a null process."""
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    adapter.stop()


def test_stop_terminates_and_waits(tmp_path: Path) -> None:
    """`stop` terminates the process and waits for it, then forgets it."""
    process = MagicMock()
    process.poll.return_value = None
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    adapter.stop()
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=ANY)
    adapter.stop()  # a second stop is again a no-op, the process forgotten


def test_restart_stops_then_starts(tmp_path: Path) -> None:
    """`restart` is `stop` then `start`, over the same data directory."""
    process = MagicMock()
    process.poll.return_value = None
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        adapter.restart()
    assert popen.call_count == 2
    process.terminate.assert_called_once()


def test_p2p_address_names_127_0_0_1_and_the_configured_port(tmp_path: Path) -> None:
    """`p2p_address` is `("127.0.0.1", p2p_port)`, the port this adapter got."""
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 4444, rpc=_FakeRpc())
    assert adapter.p2p_address == ("127.0.0.1", 4444)


def test_rpc_property_returns_a_fresh_client_each_time(tmp_path: Path) -> None:
    """`.rpc` calls `_rpc_client` again rather than caching one instance."""
    calls: list[_FakeRpc] = []

    class _CountingAdapter(_FakeAdapter):
        @override
        def _rpc_client(self) -> _FakeRpc:  # type: ignore[override]
            client = _FakeRpc()
            calls.append(client)
            return client

    adapter = _CountingAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    first = adapter.rpc
    second = adapter.rpc
    assert first is not second
    assert len(calls) == 2


def test_connect_nodes_addnodes_and_waits_for_a_connection(tmp_path: Path) -> None:
    """`connect_nodes` dials over `addnode` and polls `getnetworkinfo`.

    `getnetworkinfo` answers no connection on its first poll, so the wait
    also covers the loop's own retry -- `time.sleep` between one poll and
    the next -- rather than only the immediate-success and the
    never-succeeds paths.
    """

    class _NetworkInfoRpc(_FakeRpc):
        def __init__(self) -> None:
            super().__init__()
            self._polls = 0

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            if method == "getnetworkinfo":
                self._polls += 1
                return {"connections": 1 if self._polls > 1 else 0}
            return None

    first = _FakeAdapter(
        "fake-node", tmp_path / "first", 0, 1111, rpc=_NetworkInfoRpc()
    )
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    connect_nodes(first, second)
    assert first._rpc.calls[0] == ("addnode", ["127.0.0.1:2222", "add"])


def test_connect_nodes_raises_on_a_timeout(tmp_path: Path) -> None:
    """A connection that never shows in `getnetworkinfo` is a `TimeoutError`."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="never reported a connection"):
        connect_nodes(first, second, timeout=0.0)
