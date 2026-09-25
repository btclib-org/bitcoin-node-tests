# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_torcontrol`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_torcontrol.py` (`4556ef626754`,
2026-09-15), `test_basic` alone: `-torcontrol` is bitcoind's own
management of a Tor hidden service, the second of the charter's own two
named examples of "an option only bitcoind has a reason to carry"
(`capability.py`'s own module docstring, step 5 of issue
btclib-org/btclib#2220). No other node under this repository's reach
speaks the Tor control protocol or has a reason to, so this test carries
no `Capability` and has no `_btclib_node_test.py` counterpart --
`TF2.md`'s own per-test ledger names the row that shape takes.

A smaller claim than Core's own test, declared rather than silent:
Core's own `MockTorControlServer` answers `ADD_ONION` with a reply
advertising proof-of-work defenses, a negotiation this file's own pinned
`bitcoind` (`31.1`) never starts -- measured against `src/torcontrol.cpp`
at the `v31.1` tag, whose own `ADD_ONION` command carries no such
parameter, that half of Core's own file having landed on `master` after
`v31.1` was cut. Kept whole: the sequence a fresh onion service takes to
come up -- `PROTOCOLINFO`, `AUTHENTICATE`, `GETINFO net/listeners/socks`
and `ADD_ONION`, in that order -- over a mock Tor control server this
module ports alongside the test, exactly where Core's own file keeps it:
test infrastructure, not this repository's own harness, the plain
`socket`/`threading` choice matching `capability.py`'s own reason for
carrying no third project dependency.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import socket
import threading
import time
from typing import TYPE_CHECKING, override

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

pytestmark = pytest.mark.integration

_POLL_INTERVAL = 0.1


class _OnionBitcoindAdapter(BitcoindAdapter):
    """`BitcoindAdapter` with `-listenonion=1` where it sets `-listenonion=0`.

    `-listenonion=1` is what sends `bitcoind` to `-torcontrol` at all, as
    in Core's own `test_basic`. An `extra_args` entry cannot carry it:
    `NodeAdapter` refuses one naming an option `_command()` already sets,
    so the value is changed where it is set.
    """

    @override
    def _command(self) -> list[str]:
        """Return the base command with the onion listener turned on."""
        return [
            "-listenonion=1" if arg == "-listenonion=0" else arg
            for arg in super()._command()
        ]


class _MockTorControlServer:
    """A Tor control server answering just enough for `bitcoind` to proceed.

    Ported from Core's own `MockTorControlServer`
    (`test/functional/feature_torcontrol.py`), narrowed to the one reply
    each command of `test_basic`'s own sequence needs: a plain TCP
    listener over the standard library alone, one connection at a time.
    """

    def __init__(self, port: int) -> None:
        self.port = port
        self.received_commands: list[str] = []
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        """Listen on `127.0.0.1:port` and answer whatever connects."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.settimeout(1.0)
        self._sock.bind(("127.0.0.1", self.port))
        self._sock.listen(1)
        self._running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop serving and join the background thread."""
        self._running = False
        if self._sock is not None:
            self._sock.close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _serve(self) -> None:
        sock = self._sock
        if sock is None:  # pragma: no cover - start() always sets it first
            return
        while self._running:
            try:
                conn, _ = sock.accept()
            except OSError:
                return
            with conn:
                conn.settimeout(1.0)
                self._handle(conn)

    def _handle(self, conn: socket.socket) -> None:
        r"""Read `\r\n`-terminated commands from `conn`, answering each."""
        buf = b""
        while self._running:
            try:
                data = conn.recv(1024)
            except TimeoutError:
                continue
            except OSError:
                return
            if not data:
                return
            buf += data
            while b"\r\n" in buf:
                line, buf = buf.split(b"\r\n", 1)
                command = line.decode("utf-8").strip()
                if command:
                    self.received_commands.append(command)
                    conn.sendall(self._reply(command).encode("utf-8"))

    @staticmethod
    def _reply(command: str) -> str:
        """Return the canned reply Core's own mock server answers with."""
        if command == "PROTOCOLINFO 1":
            return (
                "250-PROTOCOLINFO 1\r\n"
                "250-AUTH METHODS=NULL\r\n"
                '250-VERSION Tor="0.1.2.3"\r\n'
                "250 OK\r\n"
            )
        if command == "AUTHENTICATE":
            return "250 OK\r\n"
        if command.startswith("ADD_ONION"):
            return (
                "250-ServiceID="
                "abcdefghijklmnopqrstuvwxyz234567abcdefghijklmnopqrstuvwxyz23\r\n"
                "250 OK\r\n"
            )
        if command.startswith("GETINFO"):
            return '250-net/listeners/socks="127.0.0.1:9050"\r\n250 OK\r\n'
        return "510 Unrecognized command\r\n"


def _wait_until(predicate: Callable[[], bool], *, timeout: float = 10.0) -> None:
    """Poll `predicate` until true, or raise once `timeout` elapses.

    :param predicate: checked every `_POLL_INTERVAL` until it answers true.
    :param timeout: how long to keep polling.
    :raises TimeoutError: `predicate` never answered true in time.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(_POLL_INTERVAL)
    if not predicate():
        err_msg = f"condition not met within {timeout} s"
        raise TimeoutError(err_msg)


def test_torcontrol_drives_a_tor_control_session_to_add_onion(
    bitcoind_path: str, tmp_path: Path
) -> None:
    """`-torcontrol` runs the real handshake against a mock Tor server.

    No `Capability` is asked for: nothing here is a fact another node
    could plausibly declare, `-torcontrol` being bitcoind's own
    management of a hidden service over Tor's own control protocol.
    """
    mock_tor = _MockTorControlServer(free_port())
    mock_tor.start()
    try:
        adapter = _OnionBitcoindAdapter(
            bitcoind_path,
            tmp_path,
            free_port(),
            free_port(),
            extra_args=(f"-torcontrol=127.0.0.1:{mock_tor.port}",),
        )
        adapter.start()
        try:
            _wait_until(lambda: len(mock_tor.received_commands) >= 4)
        finally:
            adapter.stop()
    finally:
        mock_tor.stop()

    assert mock_tor.received_commands[0] == "PROTOCOLINFO 1"
    assert mock_tor.received_commands[1] == "AUTHENTICATE"
    assert mock_tor.received_commands[2] == "GETINFO net/listeners/socks"
    assert mock_tor.received_commands[3].startswith("ADD_ONION ")
