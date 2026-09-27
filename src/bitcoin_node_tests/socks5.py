# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`Socks5Proxy`: a SOCKS5 server a node is pointed at, recording what it asks.

Core's own `Socks5Server` (`test/functional/test_framework/socks5.py`),
read rather than copied: a listener on IPv4 or IPv6 loopback, or on a
unix socket, speaking the server half of SOCKS5 (RFC 1928) and of its
username/password method (RFC 1929), which answers every `CONNECT`
with success and records it as a `Socks5Request` -- the address type,
the host, the port and the credentials the node sent -- for the test to
read back with `next_request`. `btclib` names SOCKS nowhere, so this is
tf2's harness rather than a covering module. It is a module of the
adapter rather than a class inside one test, as the mock Tor control
server of `tests/integration/feature_torcontrol_bitcoind_test.py` is,
because Core's own is framework code several of its tests share --
`feature_proxy.py`, `feature_anchors.py` and `p2p_private_broadcast.py`
among them.

A connection whose request is recorded is held open, unread, until
`close`: what Core's own server does only under its `keep_alive`
setting, which `feature_anchors.py` sets, closing it otherwise. The node
keeps the peer, and `getpeerinfo` lists it, until `close` or until the
node's own `-peertimeout` drops a peer that never answered -- bitcoind's
default is `DEFAULT_PEER_CONNECT_TIMEOUT` (`src/net.h`), a wait
`--timeout-factor` does not scale. Nothing is forwarded: the proxy is
the far end of every connection.

A protocol violation is not a request: it is queued in the request's
place and raised by the `next_request` that reaches it, rather than
leaving the test to wait out a timeout for a request that never comes.
"""

from __future__ import annotations

import contextlib
import queue
import shutil
import socket
import tempfile
import threading
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Self

from bitcoin_node_tests.timeout_factor import scaled

__all__ = [
    "AddressType",
    "Socks5Proxy",
    "Socks5Request",
]

_SOCKS_VERSION = 0x05

# RFC 1928's own method numbers, and the one it answers a client with
# where it offered none this server accepts
_NO_AUTHENTICATION = 0x00
_USERNAME_PASSWORD = 0x02
_NO_ACCEPTABLE_METHODS = 0xFF

# RFC 1929's own subnegotiation version, and its status for success
_AUTH_VERSION = 0x01
_AUTH_SUCCESS = 0x00

_CONNECT = 0x01

# a `CONNECT` answered with success: `REP` 0, and a bound address of
# 0.0.0.0:0, the reply Core's own `Socks5Connection.handle` sends
_SUCCESS_REPLY = bytes([_SOCKS_VERSION, 0x00, 0x00, 0x01, 0, 0, 0, 0, 0, 0])


class AddressType(IntEnum):
    """RFC 1928's `ATYP`: how the host of a request is spelled."""

    IPV4 = 0x01
    DOMAINNAME = 0x03
    IPV6 = 0x04


# the length of a host of each fixed-length address type
_HOST_LENGTH = {AddressType.IPV4: 4, AddressType.IPV6: 16}

# the loopback address a TCP proxy binds, by family
_LOOPBACK: dict[int, str] = {socket.AF_INET: "127.0.0.1", socket.AF_INET6: "::1"}


@dataclass(frozen=True)
class Socks5Request:
    """One `CONNECT` a client made, as the proxy received it.

    :param address_type: how `host` is spelled.
    :param host: the host octets as sent: four for `IPV4`, sixteen for
        `IPV6`, and the name itself for `DOMAINNAME`.
    :param port: the port asked for.
    :param username: the RFC 1929 username, `None` where the client
        authenticated with no method.
    :param password: the RFC 1929 password, `None` likewise.
    """

    address_type: AddressType
    host: bytes
    port: int
    username: bytes | None
    password: bytes | None


def _receive(connection: socket.socket, count: int) -> bytes:
    """Return exactly `count` octets from `connection`.

    :raises ConnectionError: the client closed the connection first.
    """
    data = b""
    while len(data) < count:
        chunk = connection.recv(count - len(data))
        if not chunk:
            err_msg = f"connection closed after {len(data)} of {count} octets"
            raise ConnectionError(err_msg)
        data += chunk
    return data


def _check_version(received: int, expected: int, what: str) -> None:
    """Refuse a version octet other than `expected`.

    :raises ValueError: `received` is not `expected`.
    """
    if received != expected:
        err_msg = f"{what} version {received}, not {expected}"
        raise ValueError(err_msg)


class Socks5Proxy:
    """A local SOCKS5 server, recording each `CONNECT` it answers.

    The contract:

    - bound at construction to `family`'s loopback address and a port the
      OS chooses -- or, for `AF_UNIX`, to a socket file in a directory of
      its own under the system's temporary directory -- and accepting
      from then on, on a thread of its own, so `endpoint` is dialable
      before the caller starts the node that dials it;
    - one connection at a time: each is negotiated to its request on that
      thread, then held open, unread, until `close`;
    - the username/password method is chosen where `authentication` is
      set and the client offers it, and no authentication otherwise,
      where the client offers that -- the choice Core's own server makes
      between its `auth` and `unauth` settings, `unauth` always on;
    - `close` stops accepting, closes every connection it holds, and
      removes a unix socket's file and directory.

    The temporary directory is the system's rather than a test's own
    `tmp_path`, as Core's `feature_proxy.py` takes its path from
    `tempfile`: a unix socket's path is bounded by the size of
    `sockaddr_un`'s own `sun_path`, which a test's own directory can
    outgrow.

    :param authentication: offer RFC 1929's username/password method.
    :param family: `AF_INET`, `AF_INET6` or `AF_UNIX`.
    :param timeout: how long `next_request` waits, and how long one
        client is given to finish its negotiation, before
        `--timeout-factor`'s own scaling (`timeout_factor.scaled`).
    """

    def __init__(
        self,
        *,
        authentication: bool = False,
        family: int = socket.AF_INET,
        timeout: float = 30.0,
    ) -> None:
        self._authentication = authentication
        self._family = family
        self._timeout = scaled(timeout)
        self._results: queue.Queue[Socks5Request | Exception] = queue.Queue()
        self._held: list[socket.socket] = []
        self._negotiating: socket.socket | None = None
        self._closing = threading.Event()
        self._directory: Path | None = None
        if family == socket.AF_UNIX:
            self._directory = Path(tempfile.mkdtemp())
            self._socket = socket.socket(family)
            self._socket.bind(str(self._directory / "socks5"))
            self._socket.listen()
        elif family in _LOOPBACK:
            self._socket = socket.create_server((_LOOPBACK[family], 0), family=family)
        else:
            err_msg = f"no SOCKS5 proxy on {family!r}"
            raise ValueError(err_msg)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    @property
    def address(self) -> tuple[str, int] | str:
        """Return the `(host, port)` a client connects to, or a unix path."""
        if self._family == socket.AF_UNIX:
            return str(self._socket.getsockname())
        host, port = self._socket.getsockname()[:2]
        return str(host), int(port)

    @property
    def endpoint(self) -> str:
        """Return this proxy as `-proxy` and `getnetworkinfo` spell it.

        `host:port`, an IPv6 host in brackets, or a socket's path behind
        Core's own `unix:` prefix (`IsUnixSocketPath`, `src/netbase.cpp`).
        """
        address = self.address
        if isinstance(address, str):
            return f"unix:{address}"
        host, port = address
        return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"

    def next_request(self) -> Socks5Request:
        """Return the oldest request not yet returned.

        :raises TimeoutError: none arrived within the wait, or a client
            stalled mid-negotiation past it, raised in its request's place.
        :raises ConnectionError: a client closed its connection before its
            request was complete.
        :raises ValueError: a client broke the protocol; the message says
            where.
        """
        try:
            result = self._results.get(timeout=self._timeout)
        except queue.Empty:
            err_msg = f"no SOCKS5 request within {self._timeout}s"
            raise TimeoutError(err_msg) from None
        if isinstance(result, Exception):
            raise result
        return result

    def close(self) -> None:
        """Stop accepting, and close every connection held open.

        A connection to the proxy's own address, in its own family, is what
        wakes the thread blocked in `accept`, the way Core's own
        `Socks5Server.stop` does. A client still negotiating is shut down
        first, so the thread returns to `accept` without waiting out that
        client's timeout; the join is bounded by the same timeout all the
        same, as Core's own `stop` bounds its handlers' joins. A unix
        socket's file goes with the directory holding it.
        """
        if self._closing.is_set():
            return
        self._closing.set()
        negotiating = self._negotiating
        if negotiating is not None:
            with contextlib.suppress(OSError):
                negotiating.shutdown(socket.SHUT_RDWR)
        with socket.socket(self._family) as waker:
            waker.connect(self._socket.getsockname())
        self._thread.join(timeout=self._timeout)
        self._socket.close()
        for connection in self._held:
            connection.close()
        if self._directory is not None:
            shutil.rmtree(self._directory)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _serve(self) -> None:
        """Accept connections until `close`, negotiating each in turn."""
        while True:
            connection, _ = self._socket.accept()
            if self._closing.is_set():
                connection.close()
                return
            connection.settimeout(self._timeout)
            self._negotiating = connection
            try:
                self._results.put(self._negotiate(connection))
            except (OSError, ValueError) as exc:
                connection.close()
                self._results.put(exc)
            else:
                self._held.append(connection)
            finally:
                self._negotiating = None

    def _negotiate(self, connection: socket.socket) -> Socks5Request:
        """Answer one client's method choice, credentials and `CONNECT`.

        :raises ValueError: the client broke the protocol, or offered no
            method this proxy accepts -- answered with RFC 1928's
            `X'FF'` before the raise.
        :raises OSError: the connection failed or timed out first.
        """
        version, method_count = _receive(connection, 2)
        _check_version(version, _SOCKS_VERSION, "SOCKS")
        methods = _receive(connection, method_count)
        if self._authentication and _USERNAME_PASSWORD in methods:
            method = _USERNAME_PASSWORD
        elif _NO_AUTHENTICATION in methods:
            method = _NO_AUTHENTICATION
        else:
            connection.sendall(bytes([_SOCKS_VERSION, _NO_ACCEPTABLE_METHODS]))
            err_msg = f"no acceptable method among {list(methods)}"
            raise ValueError(err_msg)
        connection.sendall(bytes([_SOCKS_VERSION, method]))

        username = password = None
        if method == _USERNAME_PASSWORD:
            (auth_version,) = _receive(connection, 1)
            _check_version(auth_version, _AUTH_VERSION, "username/password")
            username = _receive(connection, _receive(connection, 1)[0])
            password = _receive(connection, _receive(connection, 1)[0])
            connection.sendall(bytes([_AUTH_VERSION, _AUTH_SUCCESS]))

        version, command, _, address_type = _receive(connection, 4)
        _check_version(version, _SOCKS_VERSION, "SOCKS")
        if command != _CONNECT:
            err_msg = f"command {command}, not CONNECT"
            raise ValueError(err_msg)
        kind = AddressType(address_type)
        length = _HOST_LENGTH.get(kind) or _receive(connection, 1)[0]
        host = _receive(connection, length)
        port = int.from_bytes(_receive(connection, 2), "big")
        connection.sendall(_SUCCESS_REPLY)
        return Socks5Request(kind, host, port, username, password)
