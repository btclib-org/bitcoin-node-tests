# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak`, rewritten on this repository's own harness: bitcoind.

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
`test_obsolete_version_disconnects_the_peer` below asks for nothing.
`test_obsolete_version_is_logged` is the log half, Core's own wording for
*why* -- `peer using obsolete version` (`net_processing.cpp`), with
`peer=5` left out of the match, that number being Core's own connection
count in its longer test rather than a fact of the obsolete-version
check itself.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.p2p import ServiceFlags, Version
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

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


def test_obsolete_version_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The wire half: a version below the minimum gets the peer dropped."""
    with Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer:
        _send_obsolete_version(peer)
        peer.wait_for_disconnect()


def test_obsolete_version_is_logged(
    bitcoind_adapter: BitcoindAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: bitcoind's own wording for why it disconnected."""
    require(Capability.DEBUG_LOG, bitcoind_adapter.capabilities, skip_counts)
    with (
        Peer(bitcoind_adapter.p2p_address, _MAGIC) as peer,
        assert_debug_log(
            bitcoind_adapter.debug_log_path, ["peer using obsolete version"]
        ),
    ):
        _send_obsolete_version(peer)
        peer.wait_for_disconnect()
