# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_nulldummy`, rewritten on this harness: btclib-node.

`feature_nulldummy_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared -- the same measurement `feature_dersig_btclib_node_test.py`'s
own docstring already has -- so this counts a skip rather than a run,
before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_nulldummy_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_nulldummy_test import (
    nulldummy_is_policy_before_activation_and_consensus_after,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_nulldummy_is_policy_before_activation_and_consensus_after(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    nulldummy_is_policy_before_activation_and_consensus_after(
        btclib_node_cluster, skip_counts
    )
