# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_i2p_ports`, one body over either node.

Read from Core's `test/functional/p2p_i2p_ports.py` (`fa20275db32c`,
2025-10-21), a file of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47):
a node given `-i2psam` refuses to dial an I2P address on any port but
`0`, the one SAM 3.1 connects to, and dials the SAM bridge for one on
port `0`. Both of Core's steps are kept, in its order, each reading
Core's own `i2p` line out of the node's debug log, so the test asks for
`Capability.I2P_SAM` and `Capability.DEBUG_LOG`.

Nothing listens at the `-i2psam` endpoint, which is what Core's file
assumes of its own. Core names a port by formula, the p2p port of a node
its file never starts; the endpoint here is a port `node.free_port` has
the OS hand out, bound and closed.

`p2p_i2p_ports_bitcoind_test.py` and `p2p_i2p_ports_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
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

__all__ = ["i2p_is_dialled_on_port_zero_alone"]

# Core's own addresses, the first on a port SAM 3.1 does not use
_ARBITRARY_PORT = "zsxwyo6qcn3chqzwxnseusqgsnuw3maqnztkiypyfxtya4snkoka.b32.i2p:8333"
_PORT_ZERO = "h3r6bkn46qxftwja53pxiykntegfyfjqtnzbm6iv6r5mungmqgmq.b32.i2p:0"


def i2p_is_dialled_on_port_zero_alone(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check an I2P address is refused on port 8333 and dialled on port 0.

    Core's own `run_test`: `addnode`'s `onetry` to an address on port
    8333 is refused before the SAM bridge is reached, and one to an
    address on port 0 fails for want of the bridge.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :raises TypeError: the node declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    (node,) = cluster(1)
    require(Capability.I2P_SAM, node.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    proxy = f"127.0.0.1:{free_port()}"
    node.restart([f"-i2psam={proxy}"])

    with assert_debug_log(
        node.debug_log_path,
        [
            (
                f"Error connecting to {_ARBITRARY_PORT}, "
                "connection refused due to arbitrary port 8333"
            )
        ],
        timeout=0,
    ):
        node.rpc.call("addnode", [_ARBITRARY_PORT, "onetry"])

    with assert_debug_log(
        node.debug_log_path,
        [f"Error connecting to {_PORT_ZERO}: Cannot connect to {proxy}"],
        timeout=0,
    ):
        node.rpc.call("addnode", [_PORT_ZERO, "onetry"])
