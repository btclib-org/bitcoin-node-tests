# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksxor`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_blocksxor.py`:
`feature_blocksxor_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_blocksxor_test import (
    block_files_are_obfuscated_with_the_xor_key,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_block_files_are_obfuscated_with_the_xor_key(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: block files under the XOR key, over bitcoind."""
    block_files_are_obfuscated_with_the_xor_key(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
