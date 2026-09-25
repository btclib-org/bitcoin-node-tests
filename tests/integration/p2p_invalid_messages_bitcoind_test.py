# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_invalid_messages.py`
(`3fd68a95e68b`, 2026-04-07)'s own `test_magic_bytes` rather than ported
whole: that method is one of several `InvalidMessagesTest` runs in
sequence over one node, most needing `-whitelist=addr@127.0.0.1`
(family 3, this step's own next one) or a mined chain
(`Capability.MINE`, declared but not what this subject needs). This
rewrites `test_magic_bytes` alone, and stands in a module of its own
rather than joining `p2p_getdata`'s: Core's own test asserts two facts of
one action -- a message with the wrong network magic gets its sender
disconnected, and the reason lands in the log -- and the log family's own
rule (issue #5) is that these two are ported differently.

`test_wrong_magic_bytes_disconnects_the_peer` reads the wire: a
disconnect is `getpeerinfo`'s or, cheaper here, `Peer.receive`'s own
`ConnectionError`, so no capability is asked for and this runs -- and
passes -- on every node this step drives.

`test_wrong_magic_bytes_is_logged` is the half nothing but a log carries:
Core's own wording, `Header error: Wrong MessageStart ... received`
(`src/net.cpp`), is bitcoind's own sentence, not a fact of the protocol
itself, so this asks for `Capability.DEBUG_LOG` and is where a node
lacking it skips rather than being asked to spell an English sentence
Core never asked it to write.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.p2p import Ping
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
_WRONG_MAGIC = bytes(byte ^ 0xFF for byte in _MAGIC)


def test_wrong_magic_bytes_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a message on the wrong network gets the peer dropped."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()


def test_wrong_magic_bytes_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["Header error: Wrong MessageStart"]
        ),
    ):
        peer.handshake()
        peer.send_raw(Ping(0).to_message(_WRONG_MAGIC).serialize())
        peer.wait_for_disconnect()
