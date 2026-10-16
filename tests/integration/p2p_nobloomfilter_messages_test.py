# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_nobloomfilter_messages`'s filtered-block step, over each node.

Read from Core's `test/functional/p2p_nobloomfilter_messages.py`
(`9871fb726cb5`, 2026-07-31): a peer asking a node that does not offer
`NODE_BLOOM` for a filtered block is disconnected, and bitcoind logs why.
Core starts its node with `-peerbloomfilters=0`, which is the default, so
this node takes no option. The file's other steps are not ported here.

The step asserts two facts of one action, so it is split as the log family
splits them ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)).
The wire half reads the disconnect. Core's `getconnectioncount` check after
it is dropped: the closed socket already says the node closed it. The log
half asks for `Capability.DEBUG_LOG`.

The disconnect is in bitcoind from bitcoin/bitcoin#35832, which the pinned
release does not carry: there the request is ignored and the peer kept.
The body reads the build's own `getnetworkinfo` `version`
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)). On
an older build the wire half asserts the peer is kept, and the log half
asserts the line is not written. `_DISCONNECT_VERSION`'s own comment has the
known limit.

Each `p2p_nobloomfilter_messages_<node>_test.py` module beside this one
runs every body, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.p2p import GetData, Inventory, InventoryType

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "filtered_block_request_disconnects_the_peer",
    "filtered_block_request_is_logged",
]

_MAGIC = magic_from_chain("regtest")

_LOG_LINE = "filtered block request received when NODE_BLOOM service disabled"

# Core's own `CLIENT_VERSION` (`src/clientversion.h`), the running build's
# own `getnetworkinfo` `version`, at or past which a filtered-block request
# disconnects: `32.0`'s, the first release carrying bitcoin/bitcoin#35832
# (`9871fb726c`, merged 2026-08-04 while `master` read `31.99`). A known
# limit: a `master` build from that merge up to the move to `32.99`
# (`f3fec67c3e`, 2026-09-11) reports `319900` and disconnects, so this
# test fails against such a build
_DISCONNECT_VERSION = 320000


def _disconnects(adapter: NodeAdapter) -> bool:
    """Whether `adapter`'s node does what Core's check asserts of `master`.

    Core's own claim for every node, bitcoind before `_DISCONNECT_VERSION`
    excepted, read off its own `getnetworkinfo` `version`
    ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
    """
    if not isinstance(adapter, BitcoindAdapter):
        return True
    version = adapter.rpc.call("getnetworkinfo")["version"]
    return bool(version >= _DISCONNECT_VERSION)


def _filtered_block_request(
    adapter: NodeAdapter,
) -> GetData:
    """Return Core's `getdata` for the tip as a filtered block."""
    best = adapter.rpc.call("getbestblockhash")
    item = Inventory(InventoryType.MSG_FILTERED_BLOCK, bytes.fromhex(str(best)))
    return GetData([item])


def filtered_block_request_disconnects_the_peer(
    adapter: NodeAdapter,
) -> None:
    """Check the wire half: a filtered-block request drops the peer.

    :param adapter: a node's own adapter fixture.
    """
    disconnects = _disconnects(adapter)
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.send(_filtered_block_request(adapter))
        if disconnects:
            peer.wait_for_disconnect()
        else:
            peer.sync_with_ping()


def filtered_block_request_is_logged(
    adapter: NodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check the log half: bitcoind's own wording for why it disconnected.

    :param adapter: a node's own adapter fixture.
    :param skip_counts: the session's own tally.
    :raises TypeError: `adapter` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
    if not isinstance(adapter, BitcoindAdapter):
        err_msg = f"{type(adapter).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    disconnects = _disconnects(adapter)
    expected, unexpected = ([_LOG_LINE], []) if disconnects else ([], [_LOG_LINE])
    with Peer(adapter.p2p_address, _MAGIC) as peer:
        peer.handshake()
        with assert_debug_log(adapter.debug_log_path, expected, unexpected):
            peer.send(_filtered_block_request(adapter))
            if disconnects:
                peer.wait_for_disconnect()
            else:
                peer.sync_with_ping()
