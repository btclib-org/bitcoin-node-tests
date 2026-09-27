# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_message_capture`, one body over either node.

Read from Core's `test/functional/p2p_message_capture.py`
(`fa5f29774872`, 2025-12-16), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node started with `-capturemessages` (`Capability.CAPTURE_MESSAGES`)
writes what it exchanges with a peer to `msgs_recv.dat` and
`msgs_sent.dat`, under its chain directory's `message_capture/`, and each
file is a sequence of records Core's own `mini_parser` reads: a
timestamp, a message type padded to twelve octets, a length, and that
many octets.

Core's `mini_parser` asserts each record's type is one its framework's
`MESSAGEMAP` names; this asserts it is one a `btclib.p2p` payload class
names, a test being written in btclib's names (rule 2 of issue
btclib-org/btclib#2220). It asserts more than Core's file besides, so
that a node writing some other file there cannot pass: the directory is
named for the peer's own address as `getpeerinfo` answers it, the way
Core's `CaptureMessageToFile` (`src/net.cpp`) names it, and the received
file holds every message type the peer sent, the sent file the
`version`, `verack` and `pong` the node answered with. The peer pings
the node before it closes, since a message is captured when the node
processes it rather than when it arrives.

The node is built through `make_adapter`
(`tests/integration/conftest.py`), since the option is its first
start's.

`p2p_message_capture_bitcoind_test.py` and
`p2p_message_capture_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

import btclib.p2p
from btclib.p2p import Payload, magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["messages_are_captured_to_disk"]

# Core's own `TIME_SIZE`, `LENGTH_SIZE` and `MSGTYPE_SIZE`
_TIME_SIZE = 8
_LENGTH_SIZE = 4
_MSGTYPE_SIZE = 12

# what `Peer.handshake` and `Peer.sync_with_ping` send, and what the node
# answers them with
_SENT_BY_PEER = frozenset({"version", "wtxidrelay", "verack", "ping"})
_SENT_BY_NODE = frozenset({"version", "verack", "pong"})


def _subclasses(cls: type) -> Iterator[type]:
    """Yield every subclass of `cls`, at any depth."""
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _subclasses(subclass)


def _message_types() -> frozenset[str]:
    """Return every message type a `btclib.p2p` payload class names."""
    for module in pkgutil.iter_modules(btclib.p2p.__path__):
        importlib.import_module(f"btclib.p2p.{module.name}")
    return frozenset(
        vars(subclass)["command"]
        for subclass in _subclasses(Payload)
        if "command" in vars(subclass)
    )


def _read_types(capture: Path, known: frozenset[str]) -> set[str]:
    """Check `capture` is Core's record format; return the types it holds.

    Core's `mini_parser`: at least one record, each record's type among
    `known`, and each record's payload as long as its length says.

    :param capture: a `msgs_recv.dat` or a `msgs_sent.dat`.
    :param known: the message types a record may carry.
    """
    data = capture.read_bytes()
    assert len(data) >= _TIME_SIZE + _LENGTH_SIZE + _MSGTYPE_SIZE
    types = set()
    start = 0
    while start < len(data):
        start += _TIME_SIZE
        msg_type = data[start : start + _MSGTYPE_SIZE].rstrip(b"\x00").decode()
        assert msg_type in known
        types.add(msg_type)
        start += _MSGTYPE_SIZE
        length = int.from_bytes(data[start : start + _LENGTH_SIZE], "little")
        start += _LENGTH_SIZE
        assert len(data[start : start + length]) == length
        start += length
    return types


def messages_are_captured_to_disk(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a node under `-capturemessages` writes a peer's messages to disk.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(
        cls, executable, datadir, rpc_port, p2p_port, ["-capturemessages"]
    )
    require(Capability.CAPTURE_MESSAGES, node.capabilities, skip_counts)
    try:
        node.start()
        with Peer(node.p2p_address, magic_from_chain("regtest")) as peer:
            peer.handshake()
            peer.sync_with_ping()
            (peer_info,) = node.rpc.call("getpeerinfo")
            address = peer_info["addr"]
        wait_until(lambda: node.rpc.call("getpeerinfo") == [])

        capture = datadir / "regtest" / "message_capture" / address.replace(":", "_")
        known = _message_types()
        assert _read_types(capture / "msgs_recv.dat", known) >= _SENT_BY_PEER
        assert _read_types(capture / "msgs_sent.dat", known) >= _SENT_BY_NODE
    finally:
        node.stop()
