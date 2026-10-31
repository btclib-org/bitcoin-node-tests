# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_posix_fs_permissions`, on tf2's own harness: bitcoind.

`feature_posix_fs_permissions_test.py` beside this module is the body,
run here against bitcoind, the oracle.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_posix_fs_permissions_test import (
    chain_directory_and_log_file_are_owner_only,
)

if TYPE_CHECKING:
    from btclib_functional_tests.bitcoind import BitcoindAdapter

pytestmark = pytest.mark.integration


def test_chain_directory_and_log_file_are_owner_only(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the chain directory and log file are owner-only."""
    chain_directory_and_log_file_are_owner_only(bitcoind_adapter)
