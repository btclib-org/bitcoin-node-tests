# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_posix_fs_permissions`, on this harness: btclib-node.

`feature_posix_fs_permissions_test.py` beside this module is the body,
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/feature_posix_fs_permissions_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_posix_fs_permissions_test import (
    chain_directory_and_log_file_are_owner_only,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter

pytestmark = pytest.mark.integration


def test_chain_directory_and_log_file_are_owner_only(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the chain directory and log file are owner-only."""
    chain_directory_and_log_file_are_owner_only(btclib_node_adapter)
