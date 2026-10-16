# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_posix_fs_permissions`, one body over each node.

Read from Core's `test/functional/feature_posix_fs_permissions.py`
(`3fd68a95e68b`, 2026-04-07) rather than ported whole: the file's own
`wallets_path` check is dropped, on the charter's own "wallet ... tests
stay out" (step 5 of issue btclib-org/btclib#2220) -- this repository
starts no node wallet, so no `wallets/` directory of the node's own ever
exists to check the permissions of. Kept whole: the node's own chain
directory and its own log file are owner-only, `0700` and `0600`, disk
family alone (
[ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)).

The log file is `debug.log` for bitcoind (`BitcoindAdapter.debug_log_path`)
`history.log` for btclib-node (`BtclibNodeAdapter.log_path`) and
`btcd.log` for btcd (`BtcdAdapter.log_path`), each in the chain
directory.

Each `feature_posix_fs_permissions_<node>_test.py` module beside this
one runs it, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.btcd import BtcdAdapter
from bitcoin_node_tests.btclib_node import BtclibNodeAdapter

if TYPE_CHECKING:
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["chain_directory_and_log_file_are_owner_only"]

_OWNER_ONLY_DIR = stat.S_IFDIR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
_OWNER_ONLY_FILE = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR


def chain_directory_and_log_file_are_owner_only(
    adapter: NodeAdapter,
) -> None:
    """Check the chain directory and log file refuse group/other access.

    :param adapter: a started node.
    """
    if isinstance(adapter, BitcoindAdapter):
        log_path = adapter.debug_log_path
    else:
        assert isinstance(adapter, BtclibNodeAdapter | BtcdAdapter)
        log_path = adapter.log_path
    assert log_path.parent.lstat().st_mode == _OWNER_ONLY_DIR
    assert log_path.lstat().st_mode == _OWNER_ONLY_FILE
