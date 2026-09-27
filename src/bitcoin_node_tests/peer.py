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

`Listener` is the other direction, Core's `peer_accept_connection`: a
socket the node is made to dial, the node's own outbound connection
arriving there as a `Peer` like any other.
"""

from __future__ import annotations

import io
import secrets
import socket
import time
from collections import Counter
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
    "Listener",
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

    `message_count` is Core's `P2PInterface.message_count`: how many
    messages of each command `receive` has returned, those `wait_for`
    and `handshake` read and drop included. `last_message` is Core's
    `P2PInterface.last_message`: the latest message of each command
    `receive` has returned, kept whole for the caller to parse.
    """

    def __init__(
        self, address: tuple[str, int], magic: bytes, *, timeout: float = 30.0
    ) -> None:
        timeout = scaled(timeout)
        connection = socket.create_connection(address, timeout=timeout)
        self._adopt(connection, magic, timeout, dialled=True)

    @classmethod
    def _accepted(cls, connection: socket.socket, magic: bytes, timeout: float) -> Self:
        """Return a `Peer` over a connection the node dialled, for `Listener`.

        :param timeout: already scaled, as `Listener.__init__` scales it.
        """
        peer = cls.__new__(cls)
        peer._adopt(connection, magic, timeout, dialled=False)
        return peer

    def _adopt(
        self, connection: socket.socket, magic: bytes, timeout: float, *, dialled: bool
    ) -> None:
        """Take `connection` over, whichever side opened it."""
        connection.settimeout(timeout)
        self._socket = connection
        self._magic = magic
        self._timeout = timeout
        self._dialled = dialled
        self._buffer = b""
        self.message_count: Counter[str] = Counter()
        self.last_message: dict[str, Message] = {}

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
                self.message_count[message.command] += 1
                self.last_message[message.command] = message
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

    def sync_with_ping(self, *, timeout: float | None = None) -> None:
        """Send two `ping`s, and wait for the `pong` answering the second.

        A node processing a connection's messages in the order they
        arrive, as Core's does, answers the second `ping` only once every
        message sent ahead of the pings has been processed, and processes
        the first `ping` as a message of its own before it, so it runs its
        own send loop for this connection at least once in between. A node
        answering a `ping` ahead of the messages sent before it
        ([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410))
        guarantees neither. Core's
        `P2PInterface.sync_with_ping` is the same barrier, built the same
        way, and its `TestNode.add_p2p_connection` runs it after the
        handshake: `handshake` returns on the node's own `verack`, which
        the node sends before it has processed this peer's.

        :param timeout: how long to wait, scaled by `--timeout-factor`
            like every other explicit wait; `self._timeout` (scaled
            already, at construction) where `None`.
        :raises TimeoutError: no matching `pong` arrived in time.
        """
        # nonzero, so that the answer to the first ping never matches
        nonce = secrets.randbelow(2**64 - 1) + 1
        self.send(Ping(0))
        self.send(Ping(nonce))
        self.wait_for(
            "pong",
            predicate=lambda m: Pong.parse(m.payload).nonce == nonce,
            timeout=timeout,
        )

    def handshake(self, *, services: ServiceFlags = _SERVICES) -> Version:
        """Exchange `version`/`verack`, and return the node's own `version`.

        Core's own handshake. The side that dialled sends its `version`
        first: this peer where it dialled the node, the node where it
        dialled a `Listener`, this peer then answering the node's own
        `version` with its own, as Core's `P2PInterface.on_version` does.
        Then, once both `version`s are out, BIP339's `wtxidrelay` goes
        ahead of this peer's `verack` --
        `btclib-node`'s own handshake refuses a `verack` that arrives
        without it first (measured against `382a29fb`'s
        `p2p.callbacks.verack`, "a `verack` ahead of the
        `version`/`wtxidrelay` it depends on"), and bitcoind accepts one
        either way, so sending it is what one peer can offer both nodes.

        :param services: the services this peer's own `version` offers,
            `NODE_NETWORK | NODE_WITNESS` where not given. Core's
            `add_p2p_connection` takes the same `services`, and
            `rpc_getblockfrompeer` drops `NODE_WITNESS` from it to be a
            pre-segwit peer.
        :returns: the node's own `Version`, `nServices` and all --
            `p2p_getdata`'s own `P2PStoreBlock` reads nothing off it, but
            a later family well might.
        """
        nonce = secrets.randbelow(2**64)
        version = Version(services=services, user_agent=_USER_AGENT, nonce=nonce)
        if self._dialled:
            self.send(version)
            version_message = self.wait_for("version")
        else:
            version_message = self.wait_for("version")
            self.send(version)
        self.send(WtxidRelay())
        self.send(Verack())
        self.wait_for("verack")
        return Version.parse(version_message.payload)


class Listener:
    """A loopback socket a node is made to dial, each connection a `Peer`.

    Core's `P2PConnection.peer_accept_connection`, what its
    `TestNode.add_outbound_p2p_connection` listens with, over one blocking
    socket rather than an event loop. The contract:

    - bound at construction to `127.0.0.1` and a port the OS chooses,
      and listening from then on, so `address` is dialable before the
      caller asks the node to dial it;
    - a backlog of one: the kernel completes the node's own connection
      and queues it until `accept`, so the call that makes the node dial
      and the `accept` after it run in sequence on the caller's thread;
    - `accept` returns the next queued connection as a `Peer` whose
      `handshake` waits for the node's `version` before sending its own,
      and whose waits are this listener's `timeout`;
    - `close` stops listening and leaves every accepted `Peer` open.

    :param magic: the four octets of the message start, as `Peer`'s.
    :param timeout: how long `accept` waits, and every accepted `Peer`'s
        default wait, before `--timeout-factor`'s own scaling
        (`timeout_factor.scaled`).
    """

    def __init__(self, magic: bytes, *, timeout: float = 30.0) -> None:
        self._magic = magic
        self._timeout = scaled(timeout)
        self._socket = socket.create_server(("127.0.0.1", 0), backlog=1)
        self._socket.settimeout(self._timeout)

    @property
    def address(self) -> tuple[str, int]:
        """Return `(host, port)` this listener is bound to."""
        host, port = self._socket.getsockname()[:2]
        return str(host), int(port)

    def accept(self) -> Peer:
        """Return the next connection a node made to `address`, as a `Peer`.

        :raises TimeoutError: no connection arrived within the wait.
        """
        connection, _ = self._socket.accept()
        return Peer._accepted(connection, self._magic, self._timeout)

    def close(self) -> None:
        """Stop listening; a `Peer` already accepted stays open."""
        self._socket.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
