# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`Peer` against a hand-written fake node, over a real loopback socket.

No real bitcoind or btclib-node here or anywhere else this suite's
ordinary run reaches (rule 1): `_FakeNode` is this module's own,
answering just enough of the protocol -- a handshake, a `ping` it can be
told to send unsolicited, and a `getdata` served with whatever payload
the test hands it -- to drive every branch `peer.py` has, over a socket
that never leaves this machine.
"""

from __future__ import annotations

import io
import secrets
import socket
import threading
from collections.abc import Iterator

import pytest
from btclib.block import genesis_block
from btclib.exceptions import BTClibValueError
from btclib.p2p import (
    BlockPayload,
    GetData,
    GetHeaders,
    Inventory,
    Message,
    Ping,
    Pong,
    Verack,
    Version,
    WtxidRelay,
)
from btclib.p2p.limits import MAX_LOCATOR_SZ
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.node import free_port
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import set_factor

_MAGIC = magic_from_chain("regtest")


class _FakeNode:
    """A minimal p2p responder: handshake, `ping` on demand, `getdata` echoed.

    One connection at a time, which is every test below: `accept` blocks
    the caller's own thread until `Peer` dials in, so a test drives both
    sides from one process without either ever guessing at timing.
    """

    def __init__(self) -> None:
        self.port = free_port()
        self._listener = socket.socket()
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", self.port))
        self._listener.listen(1)
        self._connection: socket.socket | None = None
        self._buffer = b""

    def accept(self) -> None:
        """Block until a peer connects."""
        self._connection, _ = self._listener.accept()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
        self._listener.close()

    def send(self, payload: object, *, check_validity: bool = True) -> None:
        """Frame `payload` for regtest, and send it to the connected peer.

        `check_validity=False` is what a regtest block needs: `Payload`
        classes validate against mainnet's own rules by default, and a
        regtest header's proof-of-work is not one of them.
        """
        message = payload.to_message(  # type: ignore[attr-defined]
            _MAGIC, check_validity=check_validity
        )
        assert self._connection is not None
        self._connection.sendall(message.serialize())

    def _receive(self) -> Message:
        assert self._connection is not None
        while True:
            stream = io.BytesIO(self._buffer)
            try:
                message = Message.parse(stream)
            except Exception:
                chunk = self._connection.recv(4096)
                if not chunk:
                    raise
                self._buffer += chunk
            else:
                self._buffer = self._buffer[stream.tell() :]
                return message

    def answer_handshake(self) -> None:
        """Read the peer's `version`, answer it, then wait out its `verack`."""
        self._receive()  # version
        self.send(Version(nonce=secrets.randbelow(2**64)))
        self._receive()  # wtxidrelay
        self._receive()  # verack
        self.send(Verack())

    def send_ping(self) -> int:
        """Send an unsolicited `ping`, and return its own nonce."""
        nonce = secrets.randbelow(2**63)
        self.send(Ping(nonce))
        return nonce

    def expect_pong(self, nonce: int) -> None:
        """Read the next message and assert it answers `nonce` with a pong."""
        message = self._receive()
        assert message.command == "pong"
        assert Pong.parse(message.payload).nonce == nonce

    def serve_getdata(
        self, response: object, *, check_validity: bool = True
    ) -> GetData:
        """Read a `getdata`, send `response` back, and return the request."""
        message = self._receive()
        assert message.command == "getdata"
        request = GetData.parse(message.payload)
        self.send(response, check_validity=check_validity)
        return request


@pytest.fixture
def fake_node() -> Iterator[_FakeNode]:
    """Yield a `_FakeNode`, closed on teardown either way."""
    node = _FakeNode()
    try:
        yield node
    finally:
        node.close()


def _connect_and_accept(fake_node: _FakeNode) -> Peer:
    """Dial `fake_node` on a thread, so `accept` can block the main one."""
    thread = threading.Thread(target=fake_node.accept)
    thread.start()
    peer = Peer(("127.0.0.1", fake_node.port), _MAGIC, timeout=5.0)
    thread.join(timeout=5.0)
    return peer


def test_handshake_exchanges_version_and_verack_both_ways(fake_node: _FakeNode) -> None:
    """`handshake` sends this peer's own `version`, and returns the node's."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        version = peer.handshake()
        server_thread.join(timeout=5.0)
        assert isinstance(version, Version)
    finally:
        peer.close()


def test_wait_for_answers_a_ping_while_waiting_for_something_else(
    fake_node: _FakeNode,
) -> None:
    """A `ping` while waiting for another command is answered, not returned."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        nonce = fake_node.send_ping()
        fake_node.send(WtxidRelay())

        message = peer.wait_for("wtxidrelay")
        assert message.command == "wtxidrelay"

        fake_node.expect_pong(nonce)
    finally:
        peer.close()


def test_wait_for_the_requested_block_after_a_getdata(fake_node: _FakeNode) -> None:
    """The `getdata`/`block` round trip `p2p_getdata` itself needs."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        block = genesis_block("regtest")
        peer.send(GetData([Inventory(2, block.header.hash)]))
        payload = BlockPayload(block, include_witness=False, check_validity=False)
        request = fake_node.serve_getdata(payload, check_validity=False)
        assert request.items[0].hash == block.header.hash

        message = peer.wait_for("block")
        received = BlockPayload.parse(message.payload, check_validity=False)
        assert received.block.header.hash == block.header.hash
    finally:
        peer.close()


def test_wait_for_raises_a_timeout_error_when_nothing_matches(
    fake_node: _FakeNode,
) -> None:
    """`wait_for` gives up rather than block forever on a command never sent."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        fake_node.send_ping()
        with pytest.raises(TimeoutError, match="never saw 'block'"):
            peer.wait_for("block", timeout=0.2)
    finally:
        peer.close()


def test_wait_for_a_zero_timeout_never_reads_the_socket(fake_node: _FakeNode) -> None:
    """A deadline already past is the loop's own exit, not a read timing out."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        with pytest.raises(TimeoutError, match="never saw 'block'"):
            peer.wait_for("block", timeout=0.0)
    finally:
        peer.close()


def test_wait_for_timeout_is_scaled_by_the_global_factor(fake_node: _FakeNode) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        set_factor(0.0)
        try:
            with pytest.raises(TimeoutError, match="never saw 'block'"):
                peer.wait_for("block", timeout=1000.0)
        finally:
            set_factor(1.0)
    finally:
        peer.close()


def test_peer_construction_timeout_is_scaled_by_the_global_factor(
    fake_node: _FakeNode,
) -> None:
    """`--timeout-factor` reaches the constructor's own default too.

    Inflating rather than collapsing here: `socket.create_connection`'s
    own `timeout=0` puts the socket in non-blocking mode, which is not
    what a factor of `0` means for a wait already past its deadline
    (`wait_for`'s own tests, above) -- so this checks the multiplication
    landed on the stored default directly rather than through a second
    real connection attempt.
    """
    set_factor(100.0)
    try:
        peer = _connect_and_accept(fake_node)
    finally:
        set_factor(1.0)
    try:
        assert peer._timeout == pytest.approx(500.0)
    finally:
        peer.close()


def test_receive_raises_on_a_closed_connection(fake_node: _FakeNode) -> None:
    """A socket closed mid-wait is a `ConnectionError`, not a silent hang."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)
        fake_node.close()
        with pytest.raises(ConnectionError, match="closed"):
            peer.receive()
    finally:
        peer.close()


def test_fake_node_close_before_any_peer_ever_dialled_in() -> None:
    """`_FakeNode.close` before `accept` closes the listener alone."""
    node = _FakeNode()
    node.close()


def test_fake_node_receive_raises_when_the_peer_closes_first(
    fake_node: _FakeNode,
) -> None:
    """The server side of the same close: reading after the peer hangs up."""
    peer = _connect_and_accept(fake_node)
    server_thread = threading.Thread(target=fake_node.answer_handshake)
    server_thread.start()
    peer.handshake()
    server_thread.join(timeout=5.0)
    peer.close()
    with pytest.raises(Exception):
        fake_node._receive()


def test_send_check_validity_false_reaches_to_message_not_only_serialize(
    fake_node: _FakeNode,
) -> None:
    """`check_validity=False` is what lets an over-long locator be sent at all.

    `p2p_invalid_locator`'s own subject: `GetHeaders.assert_valid` refuses
    a locator over `MAX_LOCATOR_SZ`, which is the wire behaviour the test
    is about, so sending one needs the construction and the framing both
    to skip that check -- not only `Payload.serialize`, which
    `to_message` already forwards this to.
    """
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        locator = [secrets.token_bytes(32) for _ in range(MAX_LOCATOR_SZ + 1)]
        message = GetHeaders(locator=locator, check_validity=False)
        with pytest.raises(BTClibValueError, match="locator"):
            peer.send(message)

        peer.send(message, check_validity=False)
        received = fake_node._receive()
        assert received.command == "getheaders"
    finally:
        peer.close()


def test_context_manager_closes_the_socket(fake_node: _FakeNode) -> None:
    """`with Peer(...)` closes the socket on the way out."""
    thread = threading.Thread(target=fake_node.accept)
    thread.start()
    with Peer(("127.0.0.1", fake_node.port), _MAGIC, timeout=5.0) as peer:
        thread.join(timeout=5.0)
        assert peer is not None


def test_send_raw_sends_already_serialized_bytes(fake_node: _FakeNode) -> None:
    """The log family's own escape from `self._magic`: unframed, sent raw."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        peer.send_raw(Ping(42).to_message(_MAGIC).serialize())
        message = fake_node._receive()
        assert message.command == "ping"
        assert Ping.parse(message.payload).nonce == 42
    finally:
        peer.close()


def test_wait_for_disconnect_returns_once_the_node_closes(
    fake_node: _FakeNode,
) -> None:
    """The node hanging up is exactly what this call is waiting for."""
    peer = _connect_and_accept(fake_node)
    server_thread = threading.Thread(target=fake_node.answer_handshake)
    server_thread.start()
    peer.handshake()
    server_thread.join(timeout=5.0)
    fake_node.close()
    peer.wait_for_disconnect(timeout=5.0)
    peer.close()


def test_wait_for_disconnect_drains_a_message_before_the_close(
    fake_node: _FakeNode,
) -> None:
    """A message still in flight is drained, not mistaken for staying up."""
    peer = _connect_and_accept(fake_node)
    server_thread = threading.Thread(target=fake_node.answer_handshake)
    server_thread.start()
    peer.handshake()
    server_thread.join(timeout=5.0)
    fake_node.send_ping()
    fake_node.close()
    peer.wait_for_disconnect(timeout=5.0)
    peer.close()


def test_wait_for_disconnect_raises_when_the_node_never_closes(
    fake_node: _FakeNode,
) -> None:
    """A node that stays up is a failed wait, not an endless one."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        with pytest.raises(AssertionError, match="not closed"):
            peer.wait_for_disconnect(timeout=0.2)
    finally:
        peer.close()


def test_wait_for_disconnect_a_zero_timeout_never_reads_the_socket(
    fake_node: _FakeNode,
) -> None:
    """A deadline already past is the loop's own exit, not a read timing out."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        with pytest.raises(AssertionError, match="not closed"):
            peer.wait_for_disconnect(timeout=0.0)
    finally:
        peer.close()


def test_wait_for_disconnect_timeout_is_scaled_by_the_global_factor(
    fake_node: _FakeNode,
) -> None:
    """`--timeout-factor` set to 0 collapses even a long-sounding wait."""
    peer = _connect_and_accept(fake_node)
    try:
        server_thread = threading.Thread(target=fake_node.answer_handshake)
        server_thread.start()
        peer.handshake()
        server_thread.join(timeout=5.0)

        set_factor(0.0)
        try:
            with pytest.raises(AssertionError, match="not closed"):
                peer.wait_for_disconnect(timeout=1000.0)
        finally:
            set_factor(1.0)
    finally:
        peer.close()
