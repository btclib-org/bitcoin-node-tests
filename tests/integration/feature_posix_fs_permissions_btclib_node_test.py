# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_posix_fs_permissions`, on this harness: btclib-node.

The same claim `feature_posix_fs_permissions_bitcoind_test.py` makes,
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220): the node's own chain directory and its own log
file are owner-only.

Expected to fail rather than to pass or to skip -- neither an `xfail`
nor a `pytest.skip.Exception` -- so this keeps reproducing
[ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198)
rather than hiding it: measured live against `btclib-node` `main`
`b853eb46`, the chain directory and every store directory under it come
up `0755` and `history.log` comes up `0644`, the operating system's own
umask-derived default rather than the owner-only mode neither
`os.makedirs` nor the store construction sets. `TF2.md`'s per-test table
carries the verdict this failure is, not a decoration on this module.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_posix_fs_permissions_btclib_node_test.py
"""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter

pytestmark = pytest.mark.integration

_OWNER_ONLY_DIR = stat.S_IFDIR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
_OWNER_ONLY_FILE = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR


def test_chain_directory_and_log_file_are_owner_only(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the same request the bitcoind module makes."""
    chain_dir = btclib_node_adapter.log_path.parent
    assert chain_dir.lstat().st_mode == _OWNER_ONLY_DIR
    assert btclib_node_adapter.log_path.lstat().st_mode == _OWNER_ONLY_FILE
