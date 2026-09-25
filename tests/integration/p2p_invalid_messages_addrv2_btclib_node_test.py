# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same three `addrv2` checks: btclib-node.

`p2p_invalid_messages_addrv2_bitcoind_test.py`'s own docstring is where
the wire fact each of these three asks for -- the connection survives a
malformed `addrv2` -- is argued. `btclib_node.p2p.callbacks.addrv2` calls
`btclib.p2p.addrv2.AddrV2.parse` with no `try`/`except` of its own, so a
payload that fails to deserialize raises out of the callback, and
`handle_p2p`'s own `_drop` (`p2p/main.py`) discourages and stops the
connection for any `BTClibException` a callback raises -- exactly
[ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170),
which names this dispatch-level path in general, rather than
[ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)'s
own frame-level one: that raise is `frame_message`'s, ahead of every
callback, where this one is the callback's own. `test_addrv2_empty` and
`test_addrv2_too_long_address` both fail this way, reproducing #1170
rather than a defect of their own. `test_addrv2_no_addresses` raises
nothing -- a zero-entry `addrv2` is a valid, empty list -- so its own
wire half passes here exactly as it does on bitcoind.

Measured live, the failure is racy without `_sync`'s own delay: this
node dispatches a queued p2p message asynchronously
(`p2p_manager.messages`, drained by `handle_p2p`), so a `ping` sent
immediately after the malformed `addrv2` can occasionally be answered
before that dispatch has run and stopped the connection, reading as a
false pass. The delay gives the dispatch loop a turn first; it does not
change what is under test, since `_sync`'s own `ping`/`pong` exchange is
identical to the bitcoind module's otherwise.

Each `*_keeps_the_connection` test below is written exactly as its
bitcoind counterpart, and is expected to fail rather than to pass or to
skip -- neither an `xfail` nor a `pytest.skip.Exception` -- so this keeps
reproducing #1170 rather than hiding it, the convention
`p2p_invalid_messages_misbehaving_btclib_node_test.py` and
`p2p_invalid_messages_dropped_btclib_node_test.py` already hold.
`TF2.md`'s per-test table carries the verdict these failures are.

The log half is not reached by any of this: this node's own `Logger`
(`log.py`) writes English, not Core's, so `Capability.DEBUG_LOG` is not
declared (`btclib_node.py`'s own `capabilities`), and all three log tests
skip regardless of what the wire half above found.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
import time
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Message, Ping, Pong
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")

# Time for `handle_p2p`'s own async dispatch to reach the message this
# test just sent, ahead of the `ping`/`pong` sync below -- this module's
# own docstring measures why the sync alone races without it.
_DISPATCH_DELAY = 1.0


def _addrv2_message(payload: bytes) -> bytes:
    """Return the same `addrv2` message the bitcoind module builds."""
    message = Message(_MAGIC, "addrv2", payload, check_validity=False)
    return message.serialize(check_validity=False)


def _sync(peer: Peer) -> None:
    """Round-trip a `ping`, after giving this node's own dispatch a turn."""
    time.sleep(_DISPATCH_DELAY)
    nonce = secrets.randbelow(2**64)
    peer.send(Ping(nonce))
    peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)


def test_addrv2_empty_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: fails, reproducing ISS btclib-node#1170."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(b""))
        _sync(peer)


def test_addrv2_empty_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)


def test_addrv2_no_addresses_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(bytes.fromhex("00")))
        _sync(peer)


def test_addrv2_no_addresses_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)


# Core's own `test_addrv2_too_long_address`, the same payload
# `p2p_invalid_messages_addrv2_bitcoind_test.py` builds.
_TOO_LONG_ADDRESS = bytes.fromhex("0161bc66490001fd0102" + "ab" * 513 + "208d")


def test_addrv2_too_long_address_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: fails, reproducing ISS btclib-node#1170."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_addrv2_message(_TOO_LONG_ADDRESS))
        _sync(peer)


def test_addrv2_too_long_address_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
