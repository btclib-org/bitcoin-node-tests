# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_seednode`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/p2p_seednode.py`:
`p2p_seednode_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.p2p_seednode_test import (
    a_seed_node_is_asked_at_once_only_by_an_empty_address_table,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_seed_node_is_asked_at_once_only_by_an_empty_address_table(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_seed_node_is_asked_at_once_only_by_an_empty_address_table(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
