# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`Peer`: the p2p connection a test drives, over `btclib.p2p`'s codecs.

Rule 5 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220):
btclib's own `tests/integration/` fixture is not shared, and this is tf2's
own peer rather than a port of Core's `P2PInterface`
(`test/functional/test_framework/p2p.py`) -- a synchronous socket and a
receive loop over `btclib.p2p.Message`, `Version` and the rest, where
Core's own class is `asyncio.Protocol` driven from a background thread.
What is read from Core's own class, rather than copied, is the shape of
the handshake and the convenience a test wants: `handshake` sends and
waits for both sides' `version`/`verack`, and `wait_for` is `wait_until`
narrowed to "the next message of this command", auto-answering a `ping`
along the way so a caller waiting on anything else is not the one that
has to remember to.
"""

from __future__ import annotations

import io
import secrets
import socket
import time
from typing import TYPE_CHECKING, Self

from btclib.exceptions import IncompleteMessageError
from btclib.p2p import (
    Message,
    Payload,
    Ping,
    Pong,
    ServiceFlags,
    Verack,
    Version,
    WtxidRelay,
)

from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "Peer",
]

# BIP144 and BIP339: a real peer offers both, and btclib-node's own
# handshake refuses a connection that does not (measured against
# `382a29fb`'s `p2p.callbacks.version`, "we only connect to witness
# nodes"). bitcoind is more permissive, so this is what the peer offers
# either node rather than the least either happens to demand.
_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS

_USER_AGENT = b"/bitcoin-node-tests:0/"


class Peer:
    """One p2p connection to a node, driven by hand rather than by a peer.

    :param address: `(host, port)` to dial, a `NodeAdapter.p2p_address`.
    :param magic: the four octets of the message start,
        `btclib.p2p.magic_from_chain("regtest")` for every node this
        step drives.
    :param timeout: the default wait, on `handshake` and on `wait_for`,
        before `--timeout-factor`'s own scaling (`timeout_factor.scaled`).
    """

    def __init__(
        self, address: tuple[str, int], magic: bytes, *, timeout: float = 30.0
    ) -> None:
        timeout = scaled(timeout)
        self._socket = socket.create_connection(address, timeout=timeout)
        self._magic = magic
        self._timeout = timeout
        self._buffer = b""

    def close(self) -> None:
        """Close the underlying socket."""
        self._socket.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def send(self, payload: Payload, *, check_validity: bool = True) -> None:
        """Frame `payload` for this connection's own network, and send it.

        :param payload: the message to send.
        :param check_validity: forwarded to `Payload.to_message`.
            `False` is what `p2p_invalid_locator`'s own subject needs: a
            locator over `MAX_LOCATOR_SZ` is exactly the octets a node's
            own refusal is asked about, and `assert_valid` refuses to
            build one at all where this stayed `True`.
        """
        message = payload.to_message(self._magic, check_validity=check_validity)
        self._socket.sendall(message.serialize())

    def send_raw(self, data: bytes) -> None:
        """Send already-serialized bytes, bypassing this peer's own magic.

        `send` above always frames for `self._magic`, this connection's
        own network; a caller building a message with a *different*
        magic on purpose -- the log family's own tests, provoking the
        node's "wrong network" refusal -- serializes it directly
        (`payload.to_message(bad_magic).serialize()`) and hands the
        octets here instead.
        """
        self._socket.sendall(data)

    def receive(self, *, timeout: float | None = None) -> Message:
        """Return the next whole message, reading more off the socket as needed.

        :param timeout: applied to the underlying socket for every read
            this call makes; the socket's own last setting where `None`,
            which is `wait_for`'s way of holding the *overall* wait to
            its own deadline rather than resetting it on every message
            read along the way.
        :raises ConnectionError: the peer closed the connection.
        :raises TimeoutError: no octet arrived within `timeout`.
        """
        if timeout is not None:
            self._socket.settimeout(timeout)
        while True:
            stream = io.BytesIO(self._buffer)
            try:
                message = Message.parse(stream)
            except IncompleteMessageError:
                chunk = self._socket.recv(4096)
                if not chunk:
                    err_msg = "connection closed while waiting for a message"
                    raise ConnectionError(err_msg) from None
                self._buffer += chunk
            else:
                self._buffer = self._buffer[stream.tell() :]
                return message

    def wait_for(
        self,
        command: str,
        *,
        predicate: Callable[[Message], bool] | None = None,
        timeout: float | None = None,
    ) -> Message:
        """Return the next `command` message, answering a `ping` meanwhile.

        Every other message received while waiting is read and dropped,
        `ping` excepted: it is answered with the nonce it carried, so a
        caller waiting on anything else is never the one that has to
        keep the connection's own keepalive alive.

        :param command: the message name to wait for, `"version"` or
            `"block"`.
        :param predicate: an additional test the message must pass,
            beyond naming `command` -- matching a `pong`'s own nonce,
            say. Every message failing it is dropped exactly as one of
            the wrong command is.
        :param timeout: how long to wait, scaled by `--timeout-factor`
            like every other explicit wait; `self._timeout` (scaled
            already, at construction) where `None`.
        :raises TimeoutError: no matching message arrived in time.
        """
        deadline = time.monotonic() + (
            self._timeout if timeout is None else scaled(timeout)
        )
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                message = self.receive(timeout=remaining)
            except TimeoutError:
                break
            if message.command == "ping":
                self.send(Pong(Ping.parse(message.payload).nonce))
            if message.command == command and (predicate is None or predicate(message)):
                return message
        err_msg = f"never saw {command!r} within the wait"
        raise TimeoutError(err_msg)

    def wait_for_disconnect(self, *, timeout: float | None = None) -> None:
        """Block until the node closes this connection, or raise.

        The log family's own wire-observable half: a disconnect is a
        `ConnectionError` out of `receive`, so this drains and drops
        whatever the node still sends first -- a `ping`, an `addr` --
        exactly as `wait_for` does, until either the socket closes or the
        deadline passes with it still open.

        :param timeout: how long to wait, scaled by `--timeout-factor`
            like every other explicit wait; `self._timeout` (scaled
            already, at construction) where `None`.
        :raises AssertionError: the connection was still open at the
            deadline.
        """
        deadline = time.monotonic() + (
            self._timeout if timeout is None else scaled(timeout)
        )
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                self.receive(timeout=remaining)
            except ConnectionError:
                return
            except TimeoutError:
                break
        err_msg = "connection was not closed within the wait"
        raise AssertionError(err_msg)

    def handshake(self) -> Version:
        """Exchange `version`/`verack`, and return the node's own `version`.

        Core's own handshake, from the requesting side: this peer's
        `version` first, then, once the node's own `version` is in,
        BIP339's `wtxidrelay` ahead of this peer's `verack` --
        `btclib-node`'s own handshake refuses a `verack` that arrives
        without it first (measured against `382a29fb`'s
        `p2p.callbacks.verack`, "a `verack` ahead of the
        `version`/`wtxidrelay` it depends on"), and bitcoind accepts one
        either way, so sending it is what one peer can offer both nodes.

        :returns: the node's own `Version`, `nServices` and all --
            `p2p_getdata`'s own `P2PStoreBlock` reads nothing off it, but
            a later family well might.
        """
        nonce = secrets.randbelow(2**64)
        self.send(Version(services=_SERVICES, user_agent=_USER_AGENT, nonce=nonce))
        version_message = self.wait_for("version")
        self.send(WtxidRelay())
        self.send(Verack())
        self.wait_for("verack")
        return Version.parse(version_message.payload)
