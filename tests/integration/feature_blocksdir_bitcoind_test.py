# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksdir`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_blocksdir.py`:
`feature_blocksdir_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_blocksdir_test import (
    a_nonexistent_blocksdir_refuses_to_start,
    an_existing_blocksdir_holds_the_chain_in_cores_own_files,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_nonexistent_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """The oracle: the refusal the body module names, over bitcoind."""
    a_nonexistent_blocksdir_refuses_to_start(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_existing_blocksdir_holds_the_chain_in_cores_own_files(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the files the body module names, over bitcoind."""
    an_existing_blocksdir_holds_the_chain_in_cores_own_files(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
