# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addrv2_relay`'s late `sendaddrv2`, one body over either node.

Read from Core's `test/functional/p2p_addrv2_relay.py` (`fa5f29774872`,
2025-12-16): the first check of its `run_test`, a `sendaddrv2` sent once
the handshake is complete. `net_processing.cpp`'s own `SENDADDRV2` branch
logs "sendaddrv2 received after verack" and sets `fDisconnect` when
`fSuccessfullyConnected` is already set. Core asserts the log line and
waits for the disconnect, two facts of one action, each given a half of
its own (issue #5). The log half is bitcoind's own wording, gated on
`Capability.DEBUG_LOG`.

Core's own node is started with `-whitelist=addr@127.0.0.1`, a permission
that `SENDADDRV2` branch never reads, so it is dropped.

The rest of Core's file is not ported here: its relay check moves the
node's clock with `setmocktime`, and its oversized-`addrv2` check runs on
the node after that, the clock still set --
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14).
`p2p_addrv2_relay_bitcoind_test.py` and `p2p_addrv2_relay_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import SendAddrV2

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "sendaddrv2_after_verack_disconnects_the_peer",
    "sendaddrv2_after_verack_is_logged",
]

_MAGIC = magic_from_chain("regtest")


def sendaddrv2_after_verack_disconnects_the_peer(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a `sendaddrv2` after `verack` drops the peer.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(SendAddrV2())
        peer.wait_for_disconnect()


def sendaddrv2_after_verack_is_logged(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for why it disconnected.

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
        assert_debug_log(
            adapter.debug_log_path,
            ["sendaddrv2 received after verack, disconnecting peer="],
        ),
    ):
        peer.handshake()
        peer.send(SendAddrV2())
        peer.wait_for_disconnect()
