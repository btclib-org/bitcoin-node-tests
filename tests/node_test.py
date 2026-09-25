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

import sys
from pathlib import Path
from typing import TYPE_CHECKING, override
from unittest.mock import ANY, MagicMock, patch

import pytest

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import (
    NodeAdapter,
    connect_nodes,
    disconnect_nodes,
    free_port,
    traced_transport,
    wait_until_tips_agree,
)
from bitcoin_node_tests.timeout_factor import set_factor

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet
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
    with (
        patch("subprocess.Popen", return_value=_FakeProcess()),
        patch.object(node_module, "_STARTUP_TIMEOUT", 0.0),
        pytest.raises(TimeoutError, match="did not answer"),
    ):
        adapter.start()


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


def test_stop_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """`--timeout-factor` scales the wait for the process to exit too."""
    from bitcoin_node_tests import node as node_module  # noqa: PLC0415

    process = MagicMock()
    process.poll.return_value = None
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
    adapter = _FakeAdapter("fake-node", tmp_path / "node", 0, 0, rpc=_FakeRpc())
    with patch("subprocess.Popen", return_value=process) as popen:
        adapter.start()
        adapter.restart()
    assert popen.call_count == 2
    process.terminate.assert_called_once()


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
    assert first_rpc.calls[0] == ("addnode", [address, "onetry"])


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
