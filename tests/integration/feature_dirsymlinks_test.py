# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dirsymlinks`, one body over bitcoind and btclib-node.

Read from Core's `test/functional/feature_dirsymlinks.py`
(`fa5f29774872`, 2025-12-16), disk-family mechanism alone
(issue btclib-org/btclib#2220,
[ISS 7](https://github.com/btclib-org/btclib-functional-tests/issues/7)):
a node started over a datadir whose `blocks/` and `chainstate/` are
symlinks elsewhere -- a common way of putting either on its own device
-- starts exactly as it does over the plain directories.

Core's own file asks nothing else: no wallet, no node it must not import,
no capability beyond what every adapter already answers. Kept whole.

`btclib_node`'s own chainstate and block databases are each their own
`Rdict` (RocksDB) directory, measured live to open through a symlink the
same way Core's `blk*.dat` layout does: the fact is about the operating
system's own symlink resolution rather than about either store's format.

Each of `feature_dirsymlinks_bitcoind_test.py` and
`feature_dirsymlinks_btclib_node_test.py` beside this one runs it,
`tests/integration/conftest.py`'s own module docstring having how. No
`feature_dirsymlinks_btcd_test.py` does: btcd keeps its chain in
`blocks_ffldb` in the chain's directory, where `blocks` and
`chainstate` do not exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib_functional_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = ["starts_with_symlinked_blocks_and_chainstate_directories"]


def starts_with_symlinked_blocks_and_chainstate_directories(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check a restart over symlinked `blocks/` and `chainstate/` still starts.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
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
