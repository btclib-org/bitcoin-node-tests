# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dirsymlinks`, rewritten on tf2's own harness: bitcoind.

`feature_dirsymlinks_test.py` beside this module is the body, run here
against bitcoind, the oracle.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_dirsymlinks_test import (
    starts_with_symlinked_blocks_and_chainstate_directories,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_starts_with_symlinked_blocks_and_chainstate_directories(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """The oracle: a restart over symlinked directories, over bitcoind."""
    starts_with_symlinked_blocks_and_chainstate_directories(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )
