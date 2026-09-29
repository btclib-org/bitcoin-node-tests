# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_loadblock`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_loadblock.py`:
`feature_loadblock_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_loadblock_test import a_bootstrap_file_loads_the_chain

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_bootstrap_file_loads_the_chain(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a bootstrap file loaded under `-loadblock`, over bitcoind."""
    a_bootstrap_file_loads_the_chain(bitcoind_cluster, tmp_path, skip_counts)
