# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_posix_fs_permissions`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_posix_fs_permissions.py`
(`3fd68a95e68b`, 2026-04-07) rather than ported whole: the file's own
`wallets_path` check is dropped, on the charter's own "wallet ... tests
stay out" (step 5 of issue btclib-org/btclib#2220) -- this repository
starts no node wallet, so no `wallets/` directory of the node's own ever
exists to check the permissions of. Kept whole: the node's own chain
directory and its own log file are owner-only, `0700` and `0600`, disk
family alone (
[ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter

pytestmark = pytest.mark.integration

_OWNER_ONLY_DIR = stat.S_IFDIR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
_OWNER_ONLY_FILE = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR


def test_chain_directory_and_log_file_are_owner_only(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The node's own chain directory and log file refuse group/other access."""
    chain_dir = bitcoind_adapter.debug_log_path.parent
    assert chain_dir.lstat().st_mode == _OWNER_ONLY_DIR
    assert bitcoind_adapter.debug_log_path.lstat().st_mode == _OWNER_ONLY_FILE
