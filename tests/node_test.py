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

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Self, override
from unittest.mock import ANY, MagicMock, patch

import pytest
from bitcoin_core_rpc import HttpError, RpcError, RPCErrorCode

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import (
    NodeAdapter,
    connect_nodes,
    disconnect_nodes,
    free_port,
    free_ports,
    sync_all,
    traced_transport,
    wait_until,
    wait_until_disconnected,
    wait_until_mempools_agree,
    wait_until_tips_agree,
)
from bitcoin_node_tests.timeout_factor import set_factor

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from typing import IO
    from urllib.request import Request


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


class _ScriptedRpc(_FakeRpc):
    """A `_FakeRpc` raising a caller-chosen exception rather than a fixed one.

    `answers_after` always raises `ConnectionRefusedError`; the
    `RpcError`/`HttpError` branches `_wait_for_rpc` gained need a
    caller-supplied exception, in order, before the node answers.
    """

    def __init__(self, raises: Sequence[BaseException]) -> None:
        super().__init__()
        self._raises = list(raises)

    @override
    def call(self, method: str, params: list[object] | None = None) -> object:
        self.calls.append((method, params))
        if self._raises:
            raise self._raises.pop(0)
        return {"chain": "regtest"}


class _FakeProcess:
    """A `subprocess.Popen` stand-in: `poll` answers `None` until it exits."""

    def __init__(self, exit_after: int | None = None) -> None:
        self._polls = 0
        self._exit_after = exit_after
        self.killed = False

    def poll(self) -> int | None:
        self._polls += 1
        if self._exit_after is not None and self._polls > self._exit_after:
            return 1
        return None

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        return -9


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


def test_free_ports_returns_pairwise_distinct_bindable_ports() -> None:
    """Every port `free_ports` returns is free, and none repeats another."""
    import socket  # noqa: PLC0415

    ports = free_ports(3)
    assert len(set(ports)) == len(ports)
    for port in ports:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))


class _RecyclingSocket:
    """A `socket.socket` stand-in whose OS reissues a just-closed port.

    `bind` hands out the lowest of two ports (`0` and `1`) not currently
    held by another instance of this class -- modelling the one fact
    `free_port` and `free_ports` differ on: whether a port is still
    reserved by a probe that has not yet closed. Two ports are enough to
    force the collision ISS 85 measured at random in the real ephemeral
    range: `free_port` called twice closes its first probe, freeing port
    `0`, before its second one ever binds, so the second gets `0` back
    every time under this fake; `free_ports` closes neither until both
    are bound, so its second probe only ever sees port `1` still free.
    """

    _held: ClassVar[set[int]] = set()

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        self._port = -1  # not yet bound; not a member of the pool below

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        del exc_info
        self.close()

    def bind(self, address: tuple[str, int]) -> None:
        del address
        self._port = next(c for c in (0, 1) if c not in _RecyclingSocket._held)
        _RecyclingSocket._held.add(self._port)

    def getsockname(self) -> tuple[str, int]:
        return ("127.0.0.1", self._port)

    def close(self) -> None:
        _RecyclingSocket._held.discard(self._port)


def test_free_ports_does_not_repeat_a_port_the_os_would_reissue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two ports drawn together never collide, even where two drawn apart do.

    [ISS 85](https://github.com/btclib-org/bitcoin-node-tests/issues/85)'s
    own defect, reproduced under `_RecyclingSocket`'s tiny pool rather
    than left to the real ephemeral range's own odds. Two sequential
    `free_port` calls collide on port `0` every time here, its second
    probe binding only after the first has already closed and freed it;
    `free_ports(2)` holds both probes open until each is bound, so its
    second one is forced onto port `1` instead.
    """
    monkeypatch.setattr("socket.socket", _RecyclingSocket)
    _RecyclingSocket._held.clear()

    sequential = (free_port(), free_port())
    assert sequential == (0, 0)

    _RecyclingSocket._held.clear()
    together = free_ports(2)
    assert together == (0, 1)


def test_traced_transport_prints_the_call_and_forwards_the_answer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--tracerpc`'s own wrapper prints both halves and changes nothing."""
    from urllib.request import Request  # noqa: PLC0415

    request = Request("http://127.0.0.1:1234", data=b'{"method": "getblockcount"}')

    def _inner_transport(req: Request, timeout: float) -> tuple[int, bytes]:
        assert req is request
        assert timeout == 5.0
        return 200, b'{"result": 1}'

    traced = traced_transport(_inner_transport)
    status, body = traced(request, 5.0)
    assert (status, body) == (200, b'{"result": 1}')
    printed = capsys.readouterr().out
    assert "getblockcount" in printed
    assert "200" in printed
    assert "result" in printed


def test_start_waits_for_the_rpc_and_creates_the_datadir(tmp_path: Path) -> None:
    """`start` creates the data directory and blocks until the RPC answers."""
    datadir = tmp_path / "node"
    rpc = _FakeRpc(answers_after=2)
    adapter = _FakeAdapter("fake-node", datadir, 0, 0, rpc=rpc)
    with patch("subprocess.Popen", return_value=_FakeProcess()) as popen:
        adapter.start()
    popen.assert_called_once_with(["fake-node", f"-datadir={datadir}"], stderr=ANY)
    assert datadir.is_dir()
    assert rpc.calls == [("getblockchaininfo", None)] * 3


def test_start_appends_extra_args_after_the_command(tmp_path: Path) -> None:
    """`extra_args` follows `_command`'s own argv, naming no option of it."""
    datadir = tmp_path / "node"
    adapter = _FakeAdapter(
        "fake-node", datadir, 0, 0, extra_args=["-blocksdir=/elsewhere"], rpc=_FakeRpc()
    )
    with patch("subprocess.Popen", return_value=_FakeProcess()) as popen:
        adapter.start()
    popen.assert_called_once_with(
        ["fake-node", f"-datadir={datadir}", "-blocksdir=/elsewhere"], stderr=ANY
    )


class _MultiOptionAdapter(_FakeAdapter):
    """A `_command` naming several option shapes, for the checks below."""

    @override
    def _command(self) -> list[str]:
        return ["fake-node", "-regtest", f"-datadir={self._datadir}", "--rpcport=0"]


@pytest.mark.parametrize(
    "extra_arg",
    [
        "-datadir=/elsewhere",
        "--datadir=/elsewhere",
        "-regtest",
        "-noregtest",
        "--noregtest",
        "-rpcport=1",
        "--rpcport=1",
    ],
)
def test_init_refuses_extra_args_naming_a_reserved_option(
    tmp_path: Path, extra_arg: str
) -> None:
    """Each shape `_command` could set an option in is refused the same way."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -"):
        _MultiOptionAdapter(
            "fake-node", tmp_path / "node", 0, 0, extra_args=[extra_arg], rpc=_FakeRpc()
        )


def test_init_accepts_extra_args_naming_no_reserved_option(tmp_path: Path) -> None:
    """An option `_command` never sets, or no option at all, passes through."""
    extra_args = ["-blocksdir=/elsewhere", "-no", "-", "positional"]
    adapter = _MultiOptionAdapter(
        "fake-node", tmp_path / "node", 0, 0, extra_args=extra_args, rpc=_FakeRpc()
    )
    assert adapter._extra_args == tuple(extra_args)


def test_start_raises_if_the_process_exits_first(tmp_path: Path) -> None:
    """A process gone before its RPC answers is a `RuntimeError`, not a hang."""
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with (
        patch("subprocess.Popen", return_value=_FakeProcess(exit_after=0)),
        pytest.raises(RuntimeError, match="exited with 1"),
    ):
        adapter.start()


def test_start_raises_carrying_a_real_process_s_own_stderr(tmp_path: Path) -> None:
    """A real, short-lived process's own stderr rides in the `RuntimeError`.

    A real `subprocess.Popen` rather than a mock: the capture this tests
    is the redirection `start` itself sets up, which a mocked `Popen`
    never exercises.
    """

    class _StderrAdapter(_FakeAdapter):
        @override
        def _command(self) -> list[str]:
            return [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('blocksdir missing'); sys.exit(1)",
            ]

    adapter = _StderrAdapter(
        sys.executable,
        tmp_path / "node",
        free_port(),
        free_port(),
        rpc=_FakeRpc(answers_after=10**6),
    )
    with pytest.raises(RuntimeError, match="exited with 1.*blocksdir missing"):
        adapter.start()


def test_start_raises_on_a_timeout(tmp_path: Path) -> None:
    """An RPC that never answers within the deadline is a `TimeoutError`."""
    from bitcoin_node_tests import node as node_module  # noqa: PLC0415

    adapter = _FakeAdapter(
        "fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc(answers_after=10**6)
    )
    process = _FakeProcess()
    with (
        patch("subprocess.Popen", return_value=process),
        patch.object(node_module, "_STARTUP_TIMEOUT", 0.0),
        pytest.raises(TimeoutError, match="did not answer"),
    ):
        adapter.start()
    # nothing is left running: the process is killed and forgotten, so a
    # teardown's own `stop` after it has nothing to terminate
    assert process.killed
    adapter.stop()


def test_start_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """`--timeout-factor` set to 0 collapses even a real startup timeout."""
    adapter = _FakeAdapter(
        "fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc(answers_after=10**6)
    )
    set_factor(0.0)
    try:
        with (
            patch("subprocess.Popen", return_value=_FakeProcess()),
            pytest.raises(TimeoutError, match="did not answer"),
        ):
            adapter.start()
    finally:
        set_factor(1.0)


def test_start_timeout_chains_the_last_transient_rpc_failure(tmp_path: Path) -> None:
    """The `TimeoutError` carries what the node last answered, not `None`.

    Regression test for [ISS 98](https://github.com/btclib-org/bitcoin-node-tests/issues/98):
    the pre-fix `_wait_for_rpc` raised a bare `TimeoutError`, so a caller's
    own `except ... as e: e.__cause__` read `None` for every timeout, a
    permanent answer included, and there was nothing in the traceback
    saying what the node had actually been sending back.
    """
    from bitcoin_node_tests import node as node_module  # noqa: PLC0415

    rpc = _FakeRpc(answers_after=10**6)
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    with (
        patch("subprocess.Popen", return_value=_FakeProcess()),
        patch.object(node_module, "_STARTUP_TIMEOUT", 0.05),
        pytest.raises(TimeoutError, match="did not answer") as exc_info,
    ):
        adapter.start()
    assert isinstance(exc_info.value.__cause__, ConnectionRefusedError)


def test_start_raises_at_once_on_an_rpc_error_that_is_not_warmup(
    tmp_path: Path,
) -> None:
    """A node answering with a real RPC error is failed at once, not waited out.

    Regression test for [ISS 98](https://github.com/btclib-org/bitcoin-node-tests/issues/98):
    the pre-fix `_wait_for_rpc` caught every exception alike, so this waited
    out the whole startup timeout and was reported as `TimeoutError` --
    silence -- rather than as the answer the node actually sent.
    """
    error = RpcError("out of memory", RPCErrorCode.OUT_OF_MEMORY)
    rpc = _ScriptedRpc([error])
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    with (
        patch("subprocess.Popen", return_value=_FakeProcess()),
        pytest.raises(RuntimeError, match="answered its RPC with an error") as exc_info,
    ):
        adapter.start()
    assert exc_info.value.__cause__ is error
    assert rpc.calls == [("getblockchaininfo", None)]


def test_start_treats_rpc_in_warmup_as_still_starting(tmp_path: Path) -> None:
    """`-28 RPC_IN_WARMUP` is the `RpcError` code that is waited out.

    As Core's own `wait_for_rpc_connection`
    (`test_framework/test_node.py`) waits it out too.
    """
    error = RpcError("Loading block index...", RPCErrorCode.IN_WARMUP)
    rpc = _ScriptedRpc([error, error])
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    with patch("subprocess.Popen", return_value=_FakeProcess()):
        adapter.start()
    assert rpc.calls == [("getblockchaininfo", None)] * 3


@pytest.mark.parametrize("status", [401, 403])
def test_start_raises_at_once_on_an_http_401_or_403(
    tmp_path: Path, status: int
) -> None:
    """A credential no retry can fix is failed at once, not waited out."""
    error = HttpError("unauthorized", status)
    rpc = _ScriptedRpc([error])
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    with (
        patch("subprocess.Popen", return_value=_FakeProcess()),
        pytest.raises(RuntimeError, match="node refused its RPC") as exc_info,
    ):
        adapter.start()
    assert exc_info.value.__cause__ is error
    assert rpc.calls == [("getblockchaininfo", None)]


def test_start_waits_out_an_http_error_that_is_not_401_or_403(tmp_path: Path) -> None:
    """An `HttpError` other than 401/403 is waited out, not failed at once.

    A node's own startup can still resolve it on its own.
    """
    error = HttpError("service unavailable", 503)
    rpc = _ScriptedRpc([error])
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    with patch("subprocess.Popen", return_value=_FakeProcess()):
        adapter.start()
    assert rpc.calls == [("getblockchaininfo", None)] * 2


def _stderr_path(adapter: NodeAdapter) -> Path:
    """Return the file the process `adapter` holds writes its stderr to."""
    running = adapter._running
    assert running is not None
    return running.stderr_path


def test_stop_is_a_no_op_before_start(tmp_path: Path) -> None:
    """`stop` before `start` is a no-op, not a raise on a null process."""
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    adapter.stop()


def test_stop_terminates_and_waits(tmp_path: Path) -> None:
    """`stop` terminates the process and waits for it, then forgets it."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    adapter.stop()
    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=ANY)
    adapter.stop()  # a second stop is again a no-op, the process forgotten


def test_stop_raises_on_a_process_that_already_exited_non_zero(
    tmp_path: Path,
) -> None:
    """A node gone before `stop` is a crash, raised with its code and stderr."""
    process = MagicMock()
    process.poll.side_effect = [None, 3]
    process.wait.return_value = 3
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    _stderr_path(adapter).write_bytes(b"Assertion failed: boom\n")
    with pytest.raises(
        RuntimeError,
        match=r"^node process exited with 3 before stop was called -- "
        r"stderr: Assertion failed: boom$",
    ):
        adapter.stop()
    adapter.stop()  # the crashed process is forgotten too


def test_stop_raises_on_a_non_zero_exit_on_terminate(tmp_path: Path) -> None:
    """A node exiting other than cleanly on `terminate` is raised too."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = -11
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    _stderr_path(adapter).write_bytes(b"")
    with pytest.raises(
        RuntimeError, match=r"^node process exited with -11 on terminate -- stderr: $"
    ):
        adapter.stop()
    process.terminate.assert_called_once()
    adapter.stop()


def test_stop_accepts_a_process_that_already_exited_cleanly(tmp_path: Path) -> None:
    """A node already gone with code 0, as an RPC `stop` leaves it, is clean."""
    process = MagicMock()
    process.poll.side_effect = [None, 0]
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    adapter.stop()


def test_stop_accepts_stderr_beside_a_clean_exit(tmp_path: Path) -> None:
    """Stderr alone does not fail a node that exits cleanly on `terminate`."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    _stderr_path(adapter).write_bytes(b"Warning: provoked\n")
    adapter.stop()


def test_two_adapters_over_one_datadir_each_read_their_own_stderr(
    tmp_path: Path,
) -> None:
    """A second start over a running node's datadir leaves its stderr alone.

    Regression test for [ISS 105](https://github.com/btclib-org/bitcoin-node-tests/issues/105):
    the second process's own stderr goes to a file of its own, so the
    first node's `stop` reads back what the first process wrote.
    """
    datadir = tmp_path / "node"
    written = iter([b"first\n", b"second\n"])

    def _popen(argv: list[str], *, stderr: IO[bytes]) -> MagicMock:
        del argv
        stderr.write(next(written))
        process = MagicMock()
        process.poll.return_value = None
        process.wait.return_value = 3
        return process

    first = _FakeAdapter("fake-node", datadir, 0, 0, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", datadir, 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", side_effect=_popen):
        first.start()
        second.start()
    assert _stderr_path(first) != _stderr_path(second)
    assert (
        _stderr_path(first).parent == _stderr_path(second).parent == datadir / "stderr"
    )
    with pytest.raises(RuntimeError, match=r"on terminate -- stderr: first$"):
        first.stop()
    with pytest.raises(RuntimeError, match=r"on terminate -- stderr: second$"):
        second.stop()


def test_start_refuses_a_second_start_while_a_process_is_held(tmp_path: Path) -> None:
    """A second `start` raises rather than orphaning the first process."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        with pytest.raises(RuntimeError, match="^node already started"):
            adapter.start()
        assert popen.call_count == 1
        process.terminate.assert_not_called()
        adapter.stop()
        process.terminate.assert_called_once()
        adapter.start()  # a stopped adapter starts again
    assert popen.call_count == 2


def test_stop_kills_a_process_that_outlives_the_wait(tmp_path: Path) -> None:
    """A process still running after the wait is killed, then raised."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    process.wait.side_effect = [subprocess.TimeoutExpired("fake-node", 30.0), 0]
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    _stderr_path(adapter).write_bytes(b"still flushing\n")
    with pytest.raises(TimeoutError, match="killed -- stderr: still flushing"):
        adapter.stop()
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.call_count == 2
    adapter.stop()  # the killed process is forgotten too


def test_stop_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """`--timeout-factor` scales the wait for the process to exit too."""
    from bitcoin_node_tests import node as node_module  # noqa: PLC0415

    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process):
        adapter.start()
    set_factor(3.0)
    try:
        adapter.stop()
    finally:
        set_factor(1.0)
    startup_timeout = node_module._STARTUP_TIMEOUT
    process.wait.assert_called_once_with(timeout=3.0 * startup_timeout)


def test_restart_stops_then_starts(tmp_path: Path) -> None:
    """`restart` is `stop` then `start`, over the same data directory."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        adapter.restart()
    assert popen.call_count == 2
    process.terminate.assert_called_once()


def test_restart_extra_args_replace_the_constructor_s_for_that_start_only(
    tmp_path: Path,
) -> None:
    """Given `extra_args` apply to one start; the next falls back, as Core's."""
    datadir = tmp_path / "node"
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter(
        "fake-node", datadir, 0, 0, extra_args=["-uacomment=a"], rpc=_FakeRpc()
    )
    command = ["fake-node", f"-datadir={datadir}"]
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        adapter.restart(["-bantime=1234"])
        adapter.restart([])
        adapter.restart()
    assert [c.args[0] for c in popen.call_args_list] == [
        [*command, "-uacomment=a"],
        [*command, "-bantime=1234"],
        command,
        [*command, "-uacomment=a"],
    ]


def test_restart_refuses_a_reserved_option_before_stopping(tmp_path: Path) -> None:
    """A refused replacement leaves the running node running, untouched."""
    process = MagicMock()
    process.poll.return_value = None
    process.wait.return_value = 0
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        with pytest.raises(ValueError, match=r"^extra_args reuses -datadir"):
            adapter.restart(["-datadir=/elsewhere"])
    assert popen.call_count == 1
    process.terminate.assert_not_called()


def test_restart_whose_start_fails_leaves_nothing_running(tmp_path: Path) -> None:
    """A node refusing its new argv is killed and forgotten; it starts again."""
    datadir = tmp_path / "node"
    running = MagicMock()
    running.poll.return_value = None
    running.wait.return_value = 0
    refused = _FakeProcess(exit_after=0)
    adapter = _FakeAdapter("fake-node", datadir, 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", side_effect=[running, refused, running]) as popen:
        adapter.start()
        with pytest.raises(RuntimeError, match="exited with 1"):
            adapter.restart(["-bantime=x"])
        assert refused.killed
        adapter.stop()  # nothing left to terminate
        running.terminate.assert_called_once()
        adapter.start()
    assert popen.call_args.args[0] == ["fake-node", f"-datadir={datadir}"]


def test_set_mock_time_calls_setmocktime(tmp_path: Path) -> None:
    """`set_mock_time` is `setmocktime`, the timestamp its own one argument."""
    rpc = _FakeRpc()
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=rpc)
    adapter.set_mock_time(1_700_000_000)
    assert rpc.calls == [("setmocktime", [1_700_000_000])]


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


def test_wait_until_returns_once_the_predicate_is_true() -> None:
    """The wait ends the moment `predicate` answers `True`, and not before."""
    calls: list[int] = []

    def _predicate() -> bool:
        calls.append(len(calls))
        return len(calls) >= 3

    wait_until(_predicate, timeout=30.0)
    assert len(calls) == 3


def test_wait_until_raises_on_a_timeout() -> None:
    """A deadline already past skips the loop, matching `connect_nodes`."""
    with pytest.raises(TimeoutError, match="condition not met"):
        wait_until(lambda: False, timeout=0.0)


def test_wait_until_timeout_is_scaled_by_the_global_factor() -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="condition not met"):
            wait_until(lambda: False, timeout=1000.0)
    finally:
        set_factor(1.0)


class _PeerInfoSequenceRpc(_FakeRpc):
    """Answers `getpeerinfo` with each of `answers` in turn, holding the last.

    Every other method answers `_FakeRpc`'s own default, `addnode`
    included -- this is a fake for `connect_nodes`'s own `getpeerinfo`
    polls, not for the one `addnode` call ahead of them.
    """

    def __init__(self, answers: list[object]) -> None:
        super().__init__()
        self._answers = answers
        self._index = 0

    @override
    def call(self, method: str, params: list[object] | None = None) -> object:
        super().call(method, params)
        if method != "getpeerinfo":
            return None
        answer = self._answers[min(self._index, len(self._answers) - 1)]
        self._index += 1
        return answer


def test_connect_nodes_addnodes_then_waits_on_both_sides_and_their_handshake(
    tmp_path: Path,
) -> None:
    """`connect_nodes` dials over `addnode onetry`, then waits three times.

    `first`'s own `getpeerinfo` answers a non-list once (an RPC hiccup,
    covering the branch a `list` answer never reaches), then a peer
    that is not the one dialled ahead of one that is -- `getpeerinfo`
    naming more than the one peer a call is about -- still short of a
    `pong`, then the same pair again past it: bitcoind's own shape, a
    peer short of `verack` listed regardless of state. `second`'s own
    answers no peer at all, then one -- btclib-node's own shape, a peer
    only ever listed once its handshake is already done, `pong` absent
    from an entry `_wait_for_handshake` reads as already complete.
    """
    address = "127.0.0.1:2222"
    first_rpc = _PeerInfoSequenceRpc(
        [
            {"chain": "regtest"},
            [
                {"id": 50, "addr": "127.0.0.1:5000", "inbound": False},
                {
                    "id": 7,
                    "addr": address,
                    "inbound": False,
                    "bytesrecv_per_msg": {"pong": 0},
                },
            ],
            [
                {"id": 99, "addr": "127.0.0.1:8888", "inbound": True},
                {
                    "id": 7,
                    "addr": address,
                    "inbound": False,
                    "bytesrecv_per_msg": {"pong": 29},
                },
            ],
        ]
    )
    second_rpc = _PeerInfoSequenceRpc(
        [
            [],  # before_second: nothing connected yet
            [],  # first poll after dialling: still nothing
            [{"id": 3, "addr": "127.0.0.1:9999", "inbound": True}],
        ]
    )
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=first_rpc)
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=second_rpc)
    connect_nodes(first, second)
    assert first_rpc.calls[0] == ("addnode", [address, "onetry", False])


def test_connect_nodes_raises_on_a_timeout(tmp_path: Path) -> None:
    """A connection that never shows on either side is a `TimeoutError`."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="never reported a connection to"):
        connect_nodes(first, second, timeout=0.0)


def test_connect_nodes_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="never reported a connection to"):
            connect_nodes(first, second, timeout=1000.0)
    finally:
        set_factor(1.0)


def test_connect_nodes_passes_v2transport_to_addnode(tmp_path: Path) -> None:
    """A caller asking for BIP324 gets `addnode`'s own `v2transport=True`."""
    first_rpc = _FakeRpc()
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=first_rpc)
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="never reported a connection to"):
            connect_nodes(first, second, v2transport=True)
    finally:
        set_factor(1.0)
    host, port = second.p2p_address
    assert first_rpc.calls[0] == ("addnode", [f"{host}:{port}", "onetry", True])


def test_connect_nodes_raises_where_only_second_never_shows_the_peer(
    tmp_path: Path,
) -> None:
    """`first` matching but `second` never showing it is `second`'s error."""
    address = "127.0.0.1:2222"
    first_rpc = _PeerInfoSequenceRpc([[{"id": 1, "addr": address, "inbound": False}]])
    second_rpc = _PeerInfoSequenceRpc([[]])
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=first_rpc)
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=second_rpc)
    with pytest.raises(TimeoutError, match="never reported a connection from"):
        connect_nodes(first, second, timeout=0.15)


def test_connect_nodes_raises_where_the_handshake_never_completes(
    tmp_path: Path,
) -> None:
    """Both sides showing the peer, but no `pong`, is its own `TimeoutError`.

    `first`'s own handshake wait sees a non-list answer once, then a
    peer that is not the one dialled, before settling on the one that
    is with its own `pong` stuck below the bound -- every shape a poll
    can answer without ever completing the handshake.
    """
    address = "127.0.0.1:2222"
    matching_peer = {
        "id": 1,
        "addr": address,
        "inbound": False,
        "bytesrecv_per_msg": {"pong": 0},
    }
    first_rpc = _PeerInfoSequenceRpc(
        [
            [matching_peer],  # first_peer's own match, for `_wait_for_peer`
            {"chain": "regtest"},  # handshake poll: not a list at all
            [{"id": 88, "addr": "127.0.0.1:7777", "inbound": True}],  # no match
            [matching_peer],  # held: matches, but its own `pong` never arrives
        ]
    )
    second_rpc = _PeerInfoSequenceRpc(
        [[], [{"id": 3, "addr": "127.0.0.1:9999", "inbound": True}]]
    )
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=first_rpc)
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=second_rpc)
    with pytest.raises(TimeoutError, match="never completed its own handshake"):
        connect_nodes(first, second, timeout=0.5)


def test_disconnect_nodes_disconnectnodes_and_waits_for_the_peer_to_go(
    tmp_path: Path,
) -> None:
    """`disconnect_nodes` calls `disconnectnode` and polls `getpeerinfo`.

    `getpeerinfo` still names the peer on its first poll, so the wait
    also covers the loop's own retry, matching
    `test_connect_nodes_addnodes_and_waits_for_a_connection` above.
    """

    class _PeerInfoRpc(_FakeRpc):
        def __init__(self) -> None:
            super().__init__()
            self._polls = 0

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            if method == "getpeerinfo":
                self._polls += 1
                if self._polls == 1:
                    return [{"addr": "127.0.0.1:2222"}]
                return []
            return None

    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_PeerInfoRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    disconnect_nodes(first, second)
    assert first._rpc.calls[0] == ("disconnectnode", ["127.0.0.1:2222"])


def test_disconnect_nodes_ignores_a_peer_at_a_different_address(
    tmp_path: Path,
) -> None:
    """A `getpeerinfo` entry naming another address does not block the wait."""

    class _OtherPeerRpc(_FakeRpc):
        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            if method == "getpeerinfo":
                return [{"addr": "127.0.0.1:9999"}]
            return None

    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_OtherPeerRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    disconnect_nodes(first, second)


def test_disconnect_nodes_raises_on_a_timeout(tmp_path: Path) -> None:
    """A deadline already past skips the loop, matching `connect_nodes`."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="still reports a peer"):
        disconnect_nodes(first, second, timeout=0.0)


def test_disconnect_nodes_timeout_is_scaled_by_the_global_factor(
    tmp_path: Path,
) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="still reports a peer"):
            disconnect_nodes(first, second, timeout=1000.0)
    finally:
        set_factor(1.0)


def test_wait_until_disconnected_timeout_is_scaled_by_the_global_factor(
    tmp_path: Path,
) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    node = _FakeAdapter("fake-node", tmp_path / "node", 0, 1111, rpc=_FakeRpc())
    peer = _FakeAdapter("fake-node", tmp_path / "peer", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="still reports a peer"):
            wait_until_disconnected(node, peer, timeout=1000.0)
    finally:
        set_factor(1.0)


def test_wait_until_mempools_agree_timeout_is_scaled_by_the_global_factor(
    tmp_path: Path,
) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="one mempool"):
            wait_until_mempools_agree([first, second], timeout=1000.0)
    finally:
        set_factor(1.0)


def test_wait_until_tips_agree_returns_once_every_hash_matches(
    tmp_path: Path,
) -> None:
    """The wait ends the moment every node's `getbestblockhash` agrees."""

    class _TipRpc(_FakeRpc):
        def __init__(self, hashes: list[str]) -> None:
            super().__init__()
            self._hashes = iter(hashes)

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            assert method == "getbestblockhash"
            return next(self._hashes)

    first = _FakeAdapter(
        "fake-node", tmp_path / "first", 0, 1111, rpc=_TipRpc(["a", "b"])
    )
    second = _FakeAdapter(
        "fake-node", tmp_path / "second", 0, 2222, rpc=_TipRpc(["b", "b"])
    )
    wait_until_tips_agree([first, second])


def test_wait_until_tips_agree_raises_on_a_timeout(tmp_path: Path) -> None:
    """A deadline already past skips the loop, matching `connect_nodes`."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="did not converge"):
        wait_until_tips_agree([first, second], timeout=0.0)


def test_wait_until_tips_agree_timeout_is_scaled_by_the_global_factor(
    tmp_path: Path,
) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    set_factor(0.0)
    try:
        with pytest.raises(TimeoutError, match="did not converge"):
            wait_until_tips_agree([first, second], timeout=1000.0)
    finally:
        set_factor(1.0)


def test_wait_until_disconnected_returns_once_the_peer_is_gone(
    tmp_path: Path,
) -> None:
    """The wait ends once `node`'s own `getpeerinfo` drops the peer's address.

    No `disconnectnode` call of any kind: unlike `disconnect_nodes`,
    this is the wait alone, for a drop triggered some other way.
    """

    class _PeerInfoRpc(_FakeRpc):
        def __init__(self) -> None:
            super().__init__()
            self._polls = 0

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            assert method == "getpeerinfo"
            self._polls += 1
            if self._polls == 1:
                return [{"addr": "127.0.0.1:2222"}]
            return []

    node = _FakeAdapter("fake-node", tmp_path / "node", 0, 1111, rpc=_PeerInfoRpc())
    peer = _FakeAdapter("fake-node", tmp_path / "peer", 0, 2222, rpc=_FakeRpc())
    wait_until_disconnected(node, peer)
    assert node._rpc.calls == [("getpeerinfo", None)] * 2


def test_wait_until_disconnected_raises_on_a_timeout(tmp_path: Path) -> None:
    """A deadline already past skips the loop, matching `connect_nodes`."""
    node = _FakeAdapter("fake-node", tmp_path / "node", 0, 1111, rpc=_FakeRpc())
    peer = _FakeAdapter("fake-node", tmp_path / "peer", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="still reports a peer"):
        wait_until_disconnected(node, peer, timeout=0.0)


def test_wait_until_mempools_agree_returns_once_every_pool_matches(
    tmp_path: Path,
) -> None:
    """The wait ends the moment every node's `getrawmempool` set agrees."""

    class _MempoolRpc(_FakeRpc):
        def __init__(self, pools: list[list[str]]) -> None:
            super().__init__()
            self._pools = iter(pools)

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            assert method == "getrawmempool"
            return next(self._pools)

    first = _FakeAdapter(
        "fake-node", tmp_path / "first", 0, 1111, rpc=_MempoolRpc([["a"], ["a", "b"]])
    )
    second = _FakeAdapter(
        "fake-node",
        tmp_path / "second",
        0,
        2222,
        rpc=_MempoolRpc([["a", "b"], ["a", "b"]]),
    )
    wait_until_mempools_agree([first, second])


def test_wait_until_mempools_agree_raises_on_a_timeout(tmp_path: Path) -> None:
    """A deadline already past skips the loop, matching `connect_nodes`."""
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="did not converge on one mempool"):
        wait_until_mempools_agree([first, second], timeout=0.0)


def test_sync_all_waits_for_tips_then_for_mempools(tmp_path: Path) -> None:
    """`sync_all` waits for the tips first, then for the mempools."""

    class _SyncRpc(_FakeRpc):
        def __init__(self, hash_: str, pool: list[str]) -> None:
            super().__init__()
            self._hash = hash_
            self._pool = pool

        @override
        def call(self, method: str, params: list[object] | None = None) -> object:
            super().call(method, params)
            if method == "getbestblockhash":
                return self._hash
            assert method == "getrawmempool"
            return self._pool

    first = _FakeAdapter(
        "fake-node", tmp_path / "first", 0, 1111, rpc=_SyncRpc("a", ["x"])
    )
    second = _FakeAdapter(
        "fake-node", tmp_path / "second", 0, 2222, rpc=_SyncRpc("a", ["x"])
    )
    sync_all([first, second])


def test_sync_all_raises_where_the_tips_never_agree(tmp_path: Path) -> None:
    """A tip mismatch is `sync_all`'s own failure: the mempool wait never runs.

    `timeout=0.0` skips the loop before it ever calls `getbestblockhash`
    (matching `test_wait_until_tips_agree_raises_on_a_timeout`), so a
    plain `_FakeRpc` is enough: nothing here needs to answer for real.
    """
    first = _FakeAdapter("fake-node", tmp_path / "first", 0, 1111, rpc=_FakeRpc())
    second = _FakeAdapter("fake-node", tmp_path / "second", 0, 2222, rpc=_FakeRpc())
    with pytest.raises(TimeoutError, match="did not converge on one tip"):
        sync_all([first, second], timeout=0.0)
