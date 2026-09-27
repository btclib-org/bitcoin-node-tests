# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`'s redundant `verack`, one body over either node.

Read from Core's `test/functional/p2p_handshake.py` (`3fd68a95e68b`,
2026-04-07): the first check of its `run_test`, a second `verack` sent
once the handshake is complete. `net_processing.cpp`'s own `VERACK`
branch logs "ignoring redundant verack message" and returns when
`fSuccessfullyConnected` is already set, so the peer stays connected.
Core asserts the log line, and its own `send_and_ping` fails where the
connection closed instead: two facts of one action, each given a half of
its own, the log family's own rule (issue #5). The wire half round-trips
a `ping` after the second `verack`; the log half is bitcoind's own
wording, gated on `Capability.DEBUG_LOG`.

The rest of Core's file is not ported here: its service-flag and feeler
checks dial out of the node under test (Core's
`add_outbound_p2p_connection`), and its self-connection check calls
`addconnection`, which is
[ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44)'s
subject. `p2p_handshake_bitcoind_test.py` and
`p2p_handshake_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.p2p import Verack
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "redundant_verack_is_logged",
    "redundant_verack_keeps_the_connection",
]

_MAGIC = magic_from_chain("regtest")


def redundant_verack_keeps_the_connection(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a second `verack` is ignored, not disconnected.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(Verack())
        peer.sync_with_ping()


def redundant_verack_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for the `verack` it ignored.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    :raises TypeError: `adapter` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
    if not isinstance(adapter, BitcoindAdapter):
        err_msg = f"{type(adapter).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    with (
        Peer(adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(adapter.debug_log_path, ["ignoring redundant verack message"]),
    ):
        peer.handshake()
        peer.send(Verack())
        peer.sync_with_ping()
