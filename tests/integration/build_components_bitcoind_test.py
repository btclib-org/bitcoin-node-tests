# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`'s wallet probe, against what the build says of itself.

[ISS 53](https://github.com/btclib-org/bitcoin-node-tests/issues/53):
`bitcoind.py`'s own `_has_wallet` reads wallet support off the binary,
never off `test/config.ini`, and its docstring says why. A `bitcoind`
that sits in a Core build tree has that file beside it, so the two are
compared there. A `bitcoind` with no build tree beside it is taken for a
release, and a release carries the wallet: `contrib/guix/libexec/build.sh`
runs `make -C depends` with no `NO_WALLET`, so `depends/Makefile`'s own
`wallet_packages_` is non-empty and `depends/toolchain.cmake.in` sets
`ENABLE_WALLET` on, which the script's own `CONFIGFLAGS` leave alone
(read at Core's `v31.1`). Either way the test asserts whichever shape the
running build carries rather than skipping:
`btclib-org/.github`'s `reusable-integration-bitcoind.yml` fails the
required job on any skip whose reason does not start with its
`skip-reason-prefix`, and that job runs a release, installed as
`bin/bitcoind` alone.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import configparser
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def _config_ini(bitcoind_path: str) -> Path:
    """Return where a Core build tree keeps `test/config.ini` for this binary.

    `<build>/bin/bitcoind` beside `<build>/test/config.ini` is the layout
    Core's CMake writes (`src/CMakeLists.txt`'s
    `CMAKE_RUNTIME_OUTPUT_DIRECTORY`, `test/CMakeLists.txt`'s
    `configure_file`). A bare name, as `TF2_BITCOIND=bitcoind` gives, is
    looked up on `PATH` first, the way `subprocess` finds it, rather than
    against the working directory.
    """
    found = shutil.which(bitcoind_path) or bitcoind_path
    return Path(found).resolve().parent.parent / "test" / "config.ini"


def test_mine_is_declared_exactly_where_the_build_carries_the_wallet(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """`MINE` follows `ENABLE_WALLET` in a build tree, and is on for a release.

    The adapter is constructed and never started: the capability set is
    decided in `__init__`. A build configured without the wallet writes
    `ENABLE_WALLET=false` from Core's `v32.0rc1`; up to `v31.x` it writes
    the key commented out -- `test/config.ini.in` puts it behind
    `@ENABLE_WALLET_TRUE@`, which `test/CMakeLists.txt` makes `#` -- so a
    missing key reads as `False`.
    """
    config_ini = _config_ini(bitcoind_path)
    if config_ini.is_file():
        config = configparser.ConfigParser()
        config.read(config_ini)
        expected = config.getboolean("components", "ENABLE_WALLET", fallback=False)
        reason = f"{config_ini} says ENABLE_WALLET is {expected}"
    else:
        expected = True
        reason = (
            f"no test/config.ini beside {bitcoind_path}: taken for a guix"
            " release, which carries the wallet"
        )
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(BitcoindAdapter, bitcoind_path, tmp_path, rpc_port, p2p_port)
    assert (Capability.MINE in adapter.capabilities) is expected, reason
