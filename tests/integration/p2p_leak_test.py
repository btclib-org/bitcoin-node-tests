# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak`, one body per half over either node.

Read from Core's `test/functional/p2p_leak.py` (`01b8a117d2c5`,
2026-06-04)'s own closing check, "old peers are disconnected", rather
than ported whole: the rest of `P2PLeakTest.run_test` asks what a node
sends *before* a handshake completes and what a `version` message itself
carries, neither an `assert_debug_log` subject and so outside the log
family (issue #5) this step is.

Core's own check wraps the send in `assert_debug_log(["using obsolete
version 31799, disconnecting peer=5"])` and then calls
`wait_for_disconnect` -- the disconnect itself is `net_processing.cpp`'s
own `nVersion < MIN_PEER_PROTO_VERSION` (`node/protocol_version.h`,
`31800`), observable on the wire with no log at all, so
`obsolete_version_disconnects_the_peer` below asks for nothing.
`obsolete_version_is_logged` is the log half, Core's own wording for
*why* -- `peer using obsolete version` (`net_processing.cpp`), with
`peer=5` left out of the match, that number being Core's own connection
count in its longer test rather than a fact of the obsolete-version
check itself.

`p2p_leak_bitcoind_test.py` and `p2p_leak_btclib_node_test.py` run both,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.p2p import ServiceFlags, Version
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "obsolete_version_disconnects_the_peer",
    "obsolete_version_is_logged",
]

_MAGIC = magic_from_chain("regtest")
# Core's own `create_old_version`, and the exact version its test picks:
# one below `MIN_PEER_PROTO_VERSION` (`node/protocol_version.h`, 31800).
_OBSOLETE_VERSION = 31799


def _send_obsolete_version(peer: Peer) -> None:
    peer.send(
        Version(
            version=_OBSOLETE_VERSION,
            services=ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS,
            nonce=1,
        )
    )


def obsolete_version_disconnects_the_peer(
    adapter: BitcoindAdapter | BtclibNodeAdapter,
) -> None:
    """Check the wire half: a version below the minimum gets the peer dropped.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    """
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        _send_obsolete_version(peer)
        peer.wait_for_disconnect()


def obsolete_version_is_logged(
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
        assert_debug_log(adapter.debug_log_path, ["peer using obsolete version"]),
    ):
        _send_obsolete_version(peer)
        peer.wait_for_disconnect()
