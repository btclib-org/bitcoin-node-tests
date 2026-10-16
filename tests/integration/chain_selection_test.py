# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, one body over each node.

[ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63):
a node started on each chain its adapter's `chains` names answers
`getblockchaininfo` with that chain, writes its log where the adapter
reads it, accepts a connection on its p2p port, and holds no peer --
`_command`'s own isolation flags being what keep any chain but regtest
off the real network. Each `chain_selection_<node>_test.py` module
beside this one parametrizes the body over its own adapter's `chains`,
`tests/integration/conftest.py`'s own module docstring having how they
run it.
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.btcd import BtcdAdapter
from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = ["node_starts_on_the_chain_it_is_given"]


def node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    chain: str,
) -> None:
    """Check `getblockchaininfo` names the chain the adapter was built with.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param chain: one of `cls.chains`.
    """
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        cls, executable, tmp_path / "node", rpc_port, p2p_port, chain=chain
    )
    adapter.start()
    try:
        assert adapter.rpc.call("getblockchaininfo")["chain"] == chain
        assert adapter.rpc.call("getpeerinfo") == []
        if isinstance(adapter, BitcoindAdapter):
            log_path = adapter.debug_log_path
        else:
            assert isinstance(adapter, BtclibNodeAdapter | BtcdAdapter)
            log_path = adapter.log_path
        assert log_path.exists()
        with socket.create_connection(adapter.p2p_address, timeout=10):
            pass
    finally:
        adapter.stop()
