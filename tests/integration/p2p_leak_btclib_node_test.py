# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak`, rewritten on tf2's own harness: btclib-node.

`p2p_leak_bitcoind_test.py`'s own docstring is where the split this
takes `P2PLeakTest`'s closing check into is argued. `btclib-node`'s own
`p2p.callbacks.version` (`382a29fb`) refuses a peer the same way, on a
narrower and unconditional threshold -- `version_msg.version <
PROTOCOL_VERSION` (`70016`) rather than bitcoind's own `MIN_PEER_PROTO_VERSION`
(`31800`) -- so Core's own 31799 is obsolete to this node too, and the
wire half asks for nothing and passes here as well.

The log half does not: `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), this node's own log carrying no
sentence Core's wording would match, so the second test skips.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_leak_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.p2p import ServiceFlags, Version
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_MAGIC = magic_from_chain("regtest")
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
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The wire half: the same request the bitcoind module makes."""
    with Peer(btclib_node_adapter.p2p_address, _MAGIC) as peer:
        _send_obsolete_version(peer)
        peer.wait_for_disconnect()


def test_obsolete_version_is_logged(
    btclib_node_adapter: BtclibNodeAdapter,
    skip_counts: SkipCounts,
) -> None:
    """The log half: skipped, this node's own log carrying no such wording."""
    require(Capability.DEBUG_LOG, btclib_node_adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
