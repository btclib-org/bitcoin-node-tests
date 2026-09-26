# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dirsymlinks`, rewritten on this harness: btclib-node.

The same claim `feature_dirsymlinks_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
a restart over symlinked `blocks/` and `chainstate/` still starts.
`btclib_node`'s own chainstate and block databases are each their own
`Rdict` (RocksDB) directory, measured live to open through a symlink the
same way Core's `blk*.dat` layout does -- no `Capability` asked for, the
fact being about the operating system's own symlink resolution rather
than about either store's format.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_dirsymlinks_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_starts_with_symlinked_blocks_and_chainstate_directories(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """A restart over symlinked `blocks/` and `chainstate/` still starts."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, datadir, rpc_port, p2p_port
    )
    adapter.start()
    adapter.stop()

    chain_dir = datadir / "regtest"
    blocks = chain_dir / "blocks"
    chainstate = chain_dir / "chainstate"
    new_blocks = chain_dir / "new_blocks"
    new_chainstate = chain_dir / "new_chainstate"
    blocks.rename(new_blocks)
    blocks.symlink_to(new_blocks)
    chainstate.rename(new_chainstate)
    chainstate.symlink_to(new_chainstate)

    adapter.start()
    try:
        assert blocks.is_symlink()
        assert chainstate.is_symlink()
    finally:
        adapter.stop()
