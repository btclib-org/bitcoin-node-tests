# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`'s wallet probe, against a build tree's own record.

[ISS 53](https://github.com/btclib-org/bitcoin-node-tests/issues/53):
`bitcoind.py`'s own `_has_wallet` reads wallet support off the binary,
never off `test/config.ini`, and its docstring says why. A `bitcoind`
that sits in a Core build tree has that file beside it, so the two can
be compared there; a release has no such file, and the test skips.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_mine_is_declared_where_the_build_tree_enables_the_wallet(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """`MINE` is declared exactly where `[components] ENABLE_WALLET` is true.

    `<build>/bin/bitcoind` beside `<build>/test/config.ini` is the layout
    Core's CMake writes (`src/CMakeLists.txt`'s
    `CMAKE_RUNTIME_OUTPUT_DIRECTORY`, `test/CMakeLists.txt`'s
    `configure_file`). The adapter is constructed and never started: the
    capability set is decided in `__init__`.
    """
    config_ini = Path(bitcoind_path).resolve().parent.parent / "test" / "config.ini"
    if not config_ini.is_file():
        pytest.skip(f"no {config_ini}: {bitcoind_path} is not in a Core build tree")
    config = configparser.ConfigParser()
    config.read(config_ini)
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(BitcoindAdapter, bitcoind_path, tmp_path, rpc_port, p2p_port)
    has_mine = Capability.MINE in adapter.capabilities
    assert has_mine is config.getboolean("components", "ENABLE_WALLET")
