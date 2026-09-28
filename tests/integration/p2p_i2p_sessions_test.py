# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_i2p_sessions`, one body over either node.

Read from Core's `test/functional/p2p_i2p_sessions.py` (`fa5f29774872`,
2025-12-16), a file of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47):
a node given `-i2psam` dials an I2P address over a persistent SAM
session where `-i2pacceptincoming=1` and over a transient one where
`-i2pacceptincoming=0`. Both of Core's steps are kept, in its order,
each reading Core's own `i2p` line out of the node's debug log, so the
test asks for `Capability.I2P_SAM` and `Capability.DEBUG_LOG`.

Each line is read once, as soon as `addnode` returns, which is Core's own
`assert_debug_log` default. It matters for the persistent session: a node
given `-i2pacceptincoming=1` also tries to open that session on its own,
again and again while the bridge is missing, and each try writes the same
line (`CConnman::ThreadI2PAcceptIncoming`, `src/net.cpp`), so a log
polled for longer finds the line whether or not the dial wrote it.

Nothing listens at the `-i2psam` endpoint, which is what Core's file
assumes of its own. Core names a fixed port, `60000`; the endpoint here
is a port `node.free_port` has the OS hand out, bound and closed, and
both nodes are given it, as Core gives both its own.

Core's two nodes are not linked to each other here, where Core's
`setup_network` links them: neither step reads the other node.

`p2p_i2p_sessions_bitcoind_test.py` and
`p2p_i2p_sessions_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["i2pacceptincoming_chooses_a_persistent_or_a_transient_session"]

# Core's own address
_ADDRESS = "zsxwyo6qcn3chqzwxnseusqgsnuw3maqnztkiypyfxtya4snkoka.b32.i2p"


def i2pacceptincoming_chooses_a_persistent_or_a_transient_session(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-i2pacceptincoming` decides which SAM session a dial opens.

    Core's own `run_test`: `addnode`'s `onetry` to one I2P address, from
    a node given `-i2pacceptincoming=1` and then from one given
    `-i2pacceptincoming=0`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :raises TypeError: a node declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    node0, node1 = cluster(2)
    require(Capability.I2P_SAM, node0.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, node0.capabilities, skip_counts)
    if not isinstance(node0, BitcoindAdapter) or not isinstance(node1, BitcoindAdapter):
        err_msg = f"{type(node0).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    i2psam = f"-i2psam=127.0.0.1:{free_port()}"
    node0.restart([i2psam, "-i2pacceptincoming=1"])
    node1.restart([i2psam, "-i2pacceptincoming=0"])

    with assert_debug_log(
        node0.debug_log_path, ["Creating persistent I2P SAM session"], timeout=0
    ):
        node0.rpc.call("addnode", [_ADDRESS, "onetry"])

    with assert_debug_log(
        node1.debug_log_path, ["Creating transient I2P SAM session"], timeout=0
    ):
        node1.rpc.call("addnode", [_ADDRESS, "onetry"])
