# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_loadblock`, rewritten on tf2's own harness: btcd.

`feature_loadblock_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_loadblock_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_loadblock_test import a_bootstrap_file_loads_the_chain

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_bootstrap_file_loads_the_chain(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a bootstrap file under `-loadblock`, over btcd."""
    a_bootstrap_file_loads_the_chain(btcd_cluster, tmp_path, skip_counts)
