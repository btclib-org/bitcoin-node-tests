# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`fill_mempool`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/test_framework/mempool_util.py`
(`fa5f29774872`, 2025-12-16). Core's own two callers,
`mempool_package_rbf.py` and `rpc_packages.py`, each start their node
with `-maxmempool=5`; this test does the same, over `Capability.MAXMEMPOOL`,
and asserts what `fill_mempool` itself already asserts before returning --
`mempoolminfee` above `minrelaytxfee`, and the low fee-rate transaction it
sent first gone from the mempool -- rather than repeating either check.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mempool_util import fill_mempool
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def _start_adapter(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=("-maxmempool=5",),
    )
    adapter.start()
    return adapter


def test_fill_mempool_evicts_its_own_low_fee_rate_transaction(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """`fill_mempool` returns having raised nothing: the node evicted."""
    require(Capability.MAXMEMPOOL, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        fill_mempool(adapter)
    finally:
        adapter.stop()
