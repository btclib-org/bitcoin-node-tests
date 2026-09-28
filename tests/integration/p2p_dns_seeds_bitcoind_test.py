# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_dns_seeds`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/p2p_dns_seeds.py`:
`p2p_dns_seeds_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.p2p_dns_seeds_test import (
    dns_seeds_are_queried_only_when_peers_are_wanting,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_dns_seeds_are_queried_only_when_peers_are_wanting(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    dns_seeds_are_queried_only_when_peers_are_wanting(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
