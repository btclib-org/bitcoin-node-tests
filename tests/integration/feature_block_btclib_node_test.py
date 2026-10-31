# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_block`, rewritten on tf2's own harness: btclib-node.

`feature_block_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on every build, on
`Capability.TEST_ACTIVATION_HEIGHT`, which no build declares
(`feature_dersig_btclib_node_test.py` has the measurement).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_block_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_block_test import (
    blocks_are_judged,
    blocks_are_judged_and_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btclib_node import BtclibNodeAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_blocks_are_judged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    blocks_are_judged(btclib_node_cluster, skip_counts)


def test_blocks_are_judged_and_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    blocks_are_judged_and_logged(btclib_node_cluster, skip_counts)
