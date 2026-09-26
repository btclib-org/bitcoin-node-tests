# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, against a real node: btclib-node.

[ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63),
the half of `chain_selection_bitcoind_test.py` `BtclibNodeAdapter.chains`
names: a node started on each answers `getblockchaininfo` with that
chain, writes its log where the adapter reads it, accepts a connection
on its p2p port, and holds no peer --
`_command`'s own `-connect=0` being what keeps any chain but regtest off
the real network.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/chain_selection_btclib_node_test.py
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("chain", sorted(BtclibNodeAdapter.chains))
def test_node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path, chain: str
) -> None:
    """`getblockchaininfo`'s `chain` is the one the adapter was built with."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter,
        btclib_node_python,
        tmp_path / "node",
        rpc_port,
        p2p_port,
        chain=chain,
    )
    adapter.start()
    try:
        assert adapter.rpc.call("getblockchaininfo")["chain"] == chain
        assert adapter.rpc.call("getpeerinfo") == []
        assert adapter.log_path.exists()
        with socket.create_connection(adapter.p2p_address, timeout=10):
            pass
    finally:
        adapter.stop()
