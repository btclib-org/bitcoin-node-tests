# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, rewritten on this repository's harness: bitcoind.

`feature_filelock_test.py` beside this module is the body, run here
against bitcoind, the oracle.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_filelock_test import (
    second_instance_on_same_blocksdir_refuses_to_start,
    second_instance_on_same_datadir_refuses_to_start,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_second_instance_on_same_datadir_refuses_to_start(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: a second node over the same datadir is refused."""
    second_instance_on_same_datadir_refuses_to_start(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_second_instance_on_same_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a second node over the first's blocksdir is refused."""
    second_instance_on_same_blocksdir_refuses_to_start(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
