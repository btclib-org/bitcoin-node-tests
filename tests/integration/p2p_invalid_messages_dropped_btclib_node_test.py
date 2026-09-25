# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same three checks: btclib-node.

`p2p_invalid_messages_dropped_bitcoind_test.py`'s own docstring is where
the wire fact each of these three asks for -- the connection survives a
malformed message rather than being dropped -- is argued. This node does
not keep it: every one of the three reaches btclib-node's own
`P2pManager.maybe_discourage_and_disconnect`, one layer or another, where
Core only logs and continues.

`test_wrong_checksum_keeps_the_connection` and
`test_invalid_msgtype_keeps_the_connection` are one mechanism, measured
live: `Connection.run`'s own `except Exception` around `parse_messages`
(`connection.py`) discourages and stops on *any* `BTClibException` out of
`frame_message`, and `btclib.p2p.message._command_from_bytes` raises one
for an invalid command exactly the way `Message.parse`'s own checksum
check does -- so a bad checksum and an invalid message type take the same
branch to the same outcome.
[ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)
names the checksum case; this reproduces both by the same measurement, no
second issue needed for the second branch of one handler.

`test_duplicate_version_keeps_the_connection` is a different mechanism:
`handle_p2p`'s own dispatch (`p2p/main.py`) discourages and stops a
`version`/`verack`/`wtxidrelay`/`sendaddrv2` that arrives once the
connection is already `Connected`, before the `version` callback's own
"if `conn.version_message` is not `None`: return" guard is ever reached
-- the guard is live only for a repeat sent ahead of this node's own
`verack`, not after it, which is where Core's own test and this one send
theirs.
[ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)
names it.

Each `*_keeps_the_connection` test below is written exactly as its
bitcoind counterpart, and is expected to fail rather than to pass or to
skip -- neither an `xfail` nor a `pytest.skip.Exception` -- so this keeps
reproducing the two issues above rather than hiding them, the same
convention `p2p_invalid_messages_misbehaving_btclib_node_test.py` already
holds for
[ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145).
`TF2.md`'s per-test table carries the verdict these three failures are.

The log half is not reached by any of this: this node's own `Logger`
(`log.py`) writes English, not Core's, so `Capability.DEBUG_LOG` is not
declared (`btclib_node.py`'s own `capabilities`), and all three log tests
skip regardless of what the wire half above found.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Ping, Pong, Version
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_CHECKSUM_AT = 4 + 12 + 4


def _wrong_checksum_message() -> bytes:
    """Return the same corrupted `ping` the bitcoind module builds."""
    raw = Ping(0).to_message(_MAGIC).serialize()
    return raw[:_CHECKSUM_AT] + b"\xff\xff\xff\xff" + raw[_CHECKSUM_AT + 4 :]


def _invalid_msgtype_message() -> bytes:
    """Return the same corrupted `ping` the bitcoind module builds."""
    raw = Ping(0).to_message(_MAGIC).serialize()
    command_at = 4 + 2
    return raw[:command_at] + b"\x00" + raw[command_at + 1 :]


def _sync(peer: Peer) -> None:
    """Round-trip a `ping`, the same sync the bitcoind module uses."""
    nonce = secrets.randbelow(2**64)
    peer.send(Ping(nonce))
    peer.wait_for("pong", predicate=lambda m: Pong.parse(m.payload).nonce == nonce)


def test_duplicate_version_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: fails, reproducing ISS btclib-node#1133."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Version())
        _sync(peer)


def test_duplicate_version_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)


def test_wrong_checksum_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: fails, reproducing ISS btclib-node#1130."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_wrong_checksum_message())
        _sync(peer)


def test_wrong_checksum_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)


def test_invalid_msgtype_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: fails, the same mechanism as ISS btclib-node#1130."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(_invalid_msgtype_message())
        _sync(peer)


def test_invalid_msgtype_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
