# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`socks5.Socks5Proxy`, driven by a client written out octet by octet."""

from __future__ import annotations

import socket
import struct
import tempfile
import threading
import time
from pathlib import Path

import pytest

from bitcoin_node_tests.socks5 import AddressType, Socks5Proxy, Socks5Request

# a `CONNECT` answered with success, bound to 0.0.0.0:0
_SUCCESS = bytes([5, 0, 0, 1, 0, 0, 0, 0, 0, 0])


def _client(proxy: Socks5Proxy) -> socket.socket:
    """Return a connection to `proxy`, with a wait of its own."""
    address = proxy.address
    if isinstance(address, str):
        client = socket.socket(socket.AF_UNIX)
        client.connect(address)
    else:
        client = socket.create_connection(address)
    client.settimeout(5)
    return client


def _receive(client: socket.socket, count: int) -> bytes:
    """Return `count` octets the proxy sent `client`, fewer where it closed.

    A loop rather than `MSG_WAITALL`: a socket with a timeout is
    non-blocking underneath, and Linux answers a `MSG_WAITALL` read of
    one with whatever has arrived so far.
    """
    data = b""
    while len(data) < count and (chunk := client.recv(count - len(data))):
        data += chunk
    return data


def _connect(host: bytes, address_type: int = 3, port: int = 8333) -> bytes:
    """Return a `CONNECT` request, a length octet before a `DOMAINNAME`."""
    length = bytes([len(host)]) if address_type == AddressType.DOMAINNAME else b""
    return bytes([5, 1, 0, address_type]) + length + host + port.to_bytes(2, "big")


def test_a_connect_with_no_authentication_is_recorded() -> None:
    """A client offering no authentication gets it, and its request is kept."""
    with Socks5Proxy() as proxy, _client(proxy) as client:
        client.sendall(bytes([5, 1, 0]))
        assert _receive(client, 2) == bytes([5, 0])
        client.sendall(_connect(b"node.noumenon"))
        assert _receive(client, len(_SUCCESS)) == _SUCCESS
        assert proxy.next_request() == Socks5Request(
            AddressType.DOMAINNAME, b"node.noumenon", 8333, None, None
        )


@pytest.mark.parametrize(
    "family", [socket.AF_INET, socket.AF_INET6, socket.AF_UNIX], ids=str
)
def test_every_family_records_a_connect(family: int) -> None:
    """A proxy on IPv4 or IPv6 loopback, or on a unix socket, records alike."""
    with Socks5Proxy(family=family) as proxy, _client(proxy) as client:
        client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
        assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
        assert proxy.next_request().host == b"node.noumenon"


def test_endpoint_is_spelled_the_way_proxy_takes_it() -> None:
    """`host:port`, an IPv6 host in brackets, or a path behind `unix:`."""
    with Socks5Proxy() as proxy:
        address = proxy.address
        assert address == ("127.0.0.1", address[1])
        assert proxy.endpoint == f"127.0.0.1:{address[1]}"
    with Socks5Proxy(family=socket.AF_INET6) as proxy:
        address = proxy.address
        assert address == ("::1", address[1])
        assert proxy.endpoint == f"[::1]:{address[1]}"
    with Socks5Proxy(family=socket.AF_UNIX) as proxy:
        address = proxy.address
        assert isinstance(address, str)
        assert proxy.endpoint == f"unix:{address}"


def test_close_removes_a_unix_socket_and_its_directory() -> None:
    """A unix socket's file and the directory made for it go with `close`."""
    proxy = Socks5Proxy(family=socket.AF_UNIX)
    address = proxy.address
    assert isinstance(address, str)
    path = Path(address)
    assert path.is_socket()
    proxy.close()
    assert not path.parent.exists()


class _Acquired:
    """What a `Socks5Proxy` under construction opened: sockets, directories."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, parent: Path | None) -> None:
        self.sockets: list[socket.socket] = []
        self.directories: list[Path] = []
        sockets = self.sockets
        directories = self.directories
        make_directory = tempfile.mkdtemp

        class _Socket(socket.socket):
            def __init__(self, *args: object, **kwargs: object) -> None:
                super().__init__(*args, **kwargs)  # type: ignore[arg-type]
                sockets.append(self)

        def _mkdtemp() -> str:
            directory = make_directory(dir=parent)
            directories.append(Path(directory))
            return directory

        monkeypatch.setattr(socket, "socket", _Socket)
        monkeypatch.setattr(tempfile, "mkdtemp", _mkdtemp)

    def released(self) -> bool:
        """Return whether every socket is closed and every directory gone."""
        return all(s.fileno() == -1 for s in self.sockets) and not any(
            d.exists() for d in self.directories
        )


def test_a_unix_socket_failing_to_bind_leaves_nothing_behind(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A bind refused leaves no socket open and no directory behind.

    The directory is made under a parent whose path outgrows
    `sockaddr_un`'s own `sun_path`, which is what the bind refuses.
    """
    acquired = _Acquired(monkeypatch, tmp_path / ("d" * 120))
    (tmp_path / ("d" * 120)).mkdir()
    with pytest.raises(OSError, match="too long"):
        Socks5Proxy(family=socket.AF_UNIX)
    assert acquired.sockets
    assert acquired.directories
    assert acquired.released()


@pytest.mark.parametrize(
    "family", [socket.AF_INET, socket.AF_INET6, socket.AF_UNIX], ids=str
)
def test_a_thread_failing_to_start_leaves_nothing_behind(
    monkeypatch: pytest.MonkeyPatch, family: int
) -> None:
    """A serving thread that cannot start leaves no socket or directory."""
    acquired = _Acquired(monkeypatch, None)

    def _refuse(_: threading.Thread) -> None:
        err_msg = "can't start new thread"
        raise RuntimeError(err_msg)

    monkeypatch.setattr(threading.Thread, "start", _refuse)
    with pytest.raises(RuntimeError, match="can't start new thread"):
        Socks5Proxy(family=family)
    assert acquired.sockets
    assert acquired.released()


def test_a_family_with_no_loopback_is_refused() -> None:
    """A family other than the three is refused at construction."""
    with pytest.raises(ValueError, match="no SOCKS5 proxy on"):
        Socks5Proxy(family=socket.AF_UNSPEC)


def test_username_password_is_chosen_where_both_sides_offer_it() -> None:
    """RFC 1929's method is chosen where both offer it, and its pair kept."""
    with Socks5Proxy(authentication=True) as proxy, _client(proxy) as client:
        client.sendall(bytes([5, 2, 0, 2]))
        assert _receive(client, 2) == bytes([5, 2])
        client.sendall(bytes([1, 4]) + b"user" + bytes([8]) + b"password")
        assert _receive(client, 2) == bytes([1, 0])
        client.sendall(_connect(bytes([15, 61, 23, 23]), AddressType.IPV4, 1234))
        assert _receive(client, len(_SUCCESS)) == _SUCCESS
        assert proxy.next_request() == Socks5Request(
            AddressType.IPV4, bytes([15, 61, 23, 23]), 1234, b"user", b"password"
        )


@pytest.mark.parametrize(
    "authentication,offered",
    [(False, [0, 2]), (True, [0])],
    ids=["the proxy offers none", "the client offers none"],
)
def test_no_authentication_is_chosen_where_username_password_is_not(
    authentication: bool,
    offered: list[int],
) -> None:
    """No authentication is chosen where either side lacks the other."""
    host = bytes(range(16))
    with Socks5Proxy(authentication=authentication) as proxy, _client(proxy) as c:
        c.sendall(bytes([5, len(offered), *offered]))
        assert _receive(c, 2) == bytes([5, 0])
        c.sendall(_connect(host, AddressType.IPV6, 5443))
        assert _receive(c, len(_SUCCESS)) == _SUCCESS
        assert proxy.next_request() == Socks5Request(
            AddressType.IPV6, host, 5443, None, None
        )


def test_a_client_offering_no_acceptable_method_is_refused() -> None:
    """A client offering no method the proxy accepts is answered `X'FF'`."""
    with Socks5Proxy() as proxy, _client(proxy) as client:
        client.sendall(bytes([5, 1, 2]))
        assert _receive(client, 2) == bytes([5, 0xFF])
        with pytest.raises(ValueError, match="no acceptable method"):
            proxy.next_request()


@pytest.mark.parametrize(
    "octets,match",
    [
        (bytes([4, 1, 0]), "SOCKS version 4"),
        (bytes([5, 1, 2, 2, 0, 0]), "username/password version 2"),
        (bytes([5, 1, 0, 5, 2, 0, 3]), "command 2, not CONNECT"),
        (bytes([5, 1, 0, 4, 1, 0, 3]), "SOCKS version 4"),
        (bytes([5, 1, 0, 5, 1, 0, 2]), "not a valid AddressType"),
    ],
    ids=["greeting", "authentication", "command", "request", "address type"],
)
def test_a_protocol_violation_is_raised_in_place_of_a_request(
    octets: bytes, match: str
) -> None:
    """A protocol violation is raised by the `next_request` reaching it."""
    with Socks5Proxy(authentication=True) as proxy, _client(proxy) as client:
        client.sendall(octets)
        with pytest.raises(ValueError, match=match):
            proxy.next_request()


def test_a_client_closing_early_is_raised_in_place_of_a_request() -> None:
    """A client closing mid-negotiation is raised by `next_request`."""
    with Socks5Proxy() as proxy:
        with _client(proxy) as client:
            client.sendall(bytes([5, 1]))
        with pytest.raises(ConnectionError, match="after 0 of 1 octets"):
            proxy.next_request()


def test_the_proxy_serves_the_next_client_after_a_failed_one() -> None:
    """A failed negotiation leaves the proxy serving the next client."""
    with Socks5Proxy() as proxy:
        with _client(proxy) as client:
            client.sendall(bytes([4, 1]))
        with _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            with pytest.raises(ValueError, match="SOCKS version 4"):
                proxy.next_request()
            assert proxy.next_request().host == b"node.noumenon"


def test_no_request_within_the_wait_is_a_timeout() -> None:
    """`next_request` gives up after its wait."""
    with (
        Socks5Proxy(timeout=0.1) as proxy,
        pytest.raises(TimeoutError, match="no SOCKS5 request"),
    ):
        proxy.next_request()


def test_a_connection_is_held_open_until_close() -> None:
    """A negotiated connection stays open, unread, until `close`."""
    proxy = Socks5Proxy()
    with _client(proxy) as client:
        client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
        assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
        proxy.next_request()
        client.settimeout(0.2)
        with pytest.raises(TimeoutError):
            client.recv(1)
        proxy.close()
        client.settimeout(5)
        assert client.recv(1) == b""


def test_close_stops_accepting_and_a_second_close_does_nothing() -> None:
    """`close` stops the listener, and closing twice is harmless."""
    proxy = Socks5Proxy()
    address = proxy.address
    assert isinstance(address, tuple)
    proxy.close()
    proxy.close()
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(address).close()


def test_close_does_not_wait_out_a_client_still_negotiating() -> None:
    """`close` shuts a half-negotiated client, well inside its timeout."""
    proxy = Socks5Proxy(timeout=30)
    with _client(proxy) as client:
        client.sendall(bytes([5, 1, 0]))
        assert _receive(client, 2) == bytes([5, 0])
        start = time.monotonic()
        proxy.close()
        assert time.monotonic() - start < 5
        with pytest.raises(ConnectionError, match="after 0 of 4 octets"):
            proxy.next_request()


def _destination() -> socket.socket:
    """Return a loopback listener a forwarded connection is sent to."""
    server = socket.create_server(("127.0.0.1", 0))
    server.settimeout(5)
    return server


def _address(server: socket.socket) -> tuple[str, int]:
    """Return the `(host, port)` `server` listens at."""
    host, port = server.getsockname()[:2]
    return str(host), int(port)


@pytest.mark.parametrize("family", [socket.AF_INET, socket.AF_UNIX], ids=str)
def test_a_connection_is_forwarded_where_the_factory_names(family: int) -> None:
    """The factory sees the request and the client; octets go both ways."""
    calls: list[tuple[Socks5Request, str]] = []
    with _destination() as server:

        def factory(request: Socks5Request, client: str) -> tuple[str, int]:
            calls.append((request, client))
            return _address(server)

        proxy = Socks5Proxy(family=family, destinations_factory=factory)
        with proxy, _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            far, _ = server.accept()
            with far:
                client.sendall(b"version")
                assert _receive(far, 7) == b"version"
                far.sendall(b"verack")
                assert _receive(client, 6) == b"verack"
            assert client.recv(1) == b""
            request = proxy.next_request()
            assert request.host == b"node.noumenon"
            name = client.getsockname()
            expected = name if family == socket.AF_UNIX else f"127.0.0.1:{name[1]}"
            assert calls == [(request, expected)]


def test_the_client_closing_ends_the_forwarding() -> None:
    """A client closing its end closes the destination's too."""
    with _destination() as server:
        proxy = Socks5Proxy(destinations_factory=lambda *_: _address(server))
        with proxy:
            with _client(proxy) as client:
                client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
                assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
                far, _ = server.accept()
            with far:
                assert far.recv(1) == b""


def test_a_destination_reset_ends_the_forwarding() -> None:
    """A destination resetting its end closes the client's, raising nothing."""
    with _destination() as server:
        proxy = Socks5Proxy(destinations_factory=lambda *_: _address(server), timeout=1)
        with proxy, _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            far, _ = server.accept()
            # a linger on and of zero makes `close` send a reset, not a FIN
            far.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            client.sendall(b"version")
            assert _receive(far, 7) == b"version"
            far.close()
            assert client.recv(1) == b""
            assert proxy.next_request().host == b"node.noumenon"
            with pytest.raises(TimeoutError, match="no SOCKS5 request"):
                proxy.next_request()


def test_a_factory_answering_none_closes_the_connection() -> None:
    """`None` from the factory closes the client's connection."""
    with Socks5Proxy(destinations_factory=lambda *_: None, timeout=1) as proxy:
        with _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            assert client.recv(1) == b""
        assert proxy.next_request().host == b"node.noumenon"
        with pytest.raises(TimeoutError, match="no SOCKS5 request"):
            proxy.next_request()


def test_what_forwarding_raises_is_queued_behind_the_request() -> None:
    """A factory's own exception, and a refusal, follow their requests."""
    with _destination() as server:
        refused = _address(server)
    answers: list[tuple[str, int]] = [refused]

    def factory(request: Socks5Request, client: str) -> tuple[str, int]:
        if request.host == b"refused":
            return answers[0]
        err_msg = f"no destination for {request.host!r}"
        raise LookupError(err_msg)

    with (
        Socks5Proxy(destinations_factory=factory, timeout=2) as proxy,
        _client(proxy) as client,
    ):
        client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
        assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
        assert client.recv(1) == b""
        assert proxy.next_request().host == b"node.noumenon"
        with pytest.raises(LookupError, match="no destination"):
            proxy.next_request()
        with _client(proxy) as second:
            second.sendall(bytes([5, 1, 0]) + _connect(b"refused"))
            assert _receive(second, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            assert proxy.next_request().host == b"refused"
            with pytest.raises(ConnectionRefusedError):
                proxy.next_request()


def test_close_ends_a_forwarding_at_both_ends() -> None:
    """`close` ends a forwarding, closing the client's end and the far one."""
    with _destination() as server:
        proxy = Socks5Proxy(destinations_factory=lambda *_: _address(server))
        with _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            far, _ = server.accept()
            with far:
                start = time.monotonic()
                proxy.close()
                assert time.monotonic() - start < 5
                assert client.recv(1) == b""
                assert far.recv(1) == b""


@pytest.mark.parametrize("raises", [False, True], ids=["returns", "raises"])
def test_a_factory_finishing_after_close_forwards_and_queues_nothing(
    raises: bool,
) -> None:
    """A factory still running at `close` has its answer dropped."""
    entered = threading.Event()
    release = threading.Event()
    with _destination() as server:

        def factory(request: Socks5Request, client: str) -> tuple[str, int]:
            entered.set()
            release.wait(5)
            if raises:
                err_msg = "too late"
                raise LookupError(err_msg)
            return _address(server)

        proxy = Socks5Proxy(destinations_factory=factory, timeout=1)
        with _client(proxy) as client:
            client.sendall(bytes([5, 1, 0]) + _connect(b"node.noumenon"))
            assert _receive(client, 2 + len(_SUCCESS)) == bytes([5, 0]) + _SUCCESS
            assert entered.wait(5)

            def release_once_closing() -> None:
                proxy._closing.wait(5)
                release.set()

            releaser = threading.Thread(target=release_once_closing)
            releaser.start()
            proxy.close()
            releaser.join(5)
            assert client.recv(1) == b""
            if not raises:
                far, _ = server.accept()
                with far:
                    assert far.recv(1) == b""
        assert proxy.next_request().host == b"node.noumenon"
        with pytest.raises(TimeoutError, match="no SOCKS5 request"):
            proxy.next_request()


def test_a_request_negotiated_as_close_runs_is_held_and_closed() -> None:
    """A request completing once `close` has begun is closed, not forwarded."""
    called: list[Socks5Request] = []
    proxy = Socks5Proxy(destinations_factory=lambda request, _: called.append(request))
    with _client(proxy) as client:
        client.sendall(bytes([5, 1, 0]))
        assert _receive(client, 2) == bytes([5, 0])
        with proxy._lock:
            proxy._closing.set()
        client.sendall(_connect(b"node.noumenon"))
        assert _receive(client, len(_SUCCESS)) == _SUCCESS
        assert proxy.next_request().host == b"node.noumenon"
        proxy._closing.clear()
        proxy.close()
        assert client.recv(1) == b""
    assert not called
