# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addr_relay`'s oversized `addr`, one body over either node.

Read from Core's `test/functional/p2p_addr_relay.py` (`b7211ba80cde`,
2026-09-22): `oversized_addr_test`, the first check of its `run_test`.
An `addr` over `MAX_ADDR_TO_SEND` entries reaches `net_processing.cpp`'s
own `Misbehaving` call, which schedules a disconnect; Core asserts the
`Misbehaving` wording and waits for the disconnect, two facts of one
action, each given a half of its own (issue #5). The log half is
bitcoind's own wording, gated on `Capability.DEBUG_LOG`.

Core's own node is started with `-whitelist=addr@127.0.0.1`. That
permission is `NetPermissionFlags::Addr` alone, not `NoBan`, so it does
not exempt this connection from the disconnect `Misbehaving` schedules,
and dropping it is the narrowing
`p2p_invalid_messages_misbehaving_bitcoind_test.py`'s own docstring argues
for the same permission. Core's entries are distinct addresses; the size
check runs before any entry is stored, so these are one default entry
repeated, one over the bound where Core's own count is ten over it.

The rest of Core's file is not ported here: it moves the node's clock
with `setmocktime`, dials out of the node (Core's
`add_outbound_p2p_connection`), or both --
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14) and
[ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44).
`p2p_addr_relay_bitcoind_test.py` and `p2p_addr_relay_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.p2p import Addr, TimestampedNetworkAddress
from btclib.p2p.limits import MAX_ADDR_TO_SEND
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "oversized_addr_disconnects_the_peer",
    "oversized_addr_is_logged",
]

_MAGIC = magic_from_chain("regtest")


def _oversized_addr() -> Addr:
    """Return an `addr` one entry over `MAX_ADDR_TO_SEND`, unchecked."""
    return Addr(
        [TimestampedNetworkAddress()] * (MAX_ADDR_TO_SEND + 1), check_validity=False
    )


def oversized_addr_disconnects_the_peer(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: an `addr` over `MAX_ADDR_TO_SEND` drops the peer.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_oversized_addr(), check_validity=False)
        peer.wait_for_disconnect()


def oversized_addr_is_logged(
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
            ["Misbehaving", f"addr message size = {MAX_ADDR_TO_SEND + 1}"],
        ),
    ):
        peer.handshake()
        peer.send(_oversized_addr(), check_validity=False)
        peer.wait_for_disconnect()
