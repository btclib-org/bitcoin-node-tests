# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`socks5.Socks5Proxy`, driven by a client written out octet by octet."""

from __future__ import annotations

import socket
import time

import pytest

from bitcoin_node_tests.socks5 import AddressType, Socks5Proxy, Socks5Request

# a `CONNECT` answered with success, bound to 0.0.0.0:0
_SUCCESS = bytes([5, 0, 0, 1, 0, 0, 0, 0, 0, 0])


def _client(proxy: Socks5Proxy) -> socket.socket:
    """Return a connection to `proxy`, with a wait of its own."""
    client = socket.create_connection(proxy.address)
    client.settimeout(5)
    return client


def _receive(client: socket.socket, count: int) -> bytes:
    """Return `count` octets the proxy sent `client`, fewer where it closed."""
    return client.recv(count, socket.MSG_WAITALL)


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
    assert address[0] == "127.0.0.1"
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
