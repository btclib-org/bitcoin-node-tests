# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_csv_activation`, rewritten on this harness: btclib-node.

The same request `feature_csv_activation_bitcoind_test.py` makes,
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared -- the same measurement `feature_dersig_btclib_node_test.py`'s
own docstring already has -- so this counts a skip rather than a run,
before any node is ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_csv_activation_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_csv_activates_one_block_before_the_configured_height(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
