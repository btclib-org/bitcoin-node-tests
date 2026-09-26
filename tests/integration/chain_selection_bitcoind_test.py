# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, against a real node: bitcoind.

[ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63):
a node started on each chain `BitcoindAdapter.chains` names answers
`getblockchaininfo` with that chain, writes its cookie and its log where
the adapter reads them, accepts a connection on its p2p port, and holds
no peer -- `_command`'s own
`-connect=0`, `-dnsseed=0` and `-fixedseeds=0` being what keeps any chain
but regtest off the real network.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("chain", sorted(BitcoindAdapter.chains))
def test_node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path, chain: str
) -> None:
    """`getblockchaininfo`'s `chain` is the one the adapter was built with."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path / "node",
        rpc_port,
        p2p_port,
        chain=chain,
    )
    adapter.start()
    try:
        assert adapter.rpc.call("getblockchaininfo")["chain"] == chain
        assert adapter.rpc.call("getpeerinfo") == []
        assert adapter.debug_log_path.exists()
        with socket.create_connection(adapter.p2p_address, timeout=10):
            pass
    finally:
        adapter.stop()
