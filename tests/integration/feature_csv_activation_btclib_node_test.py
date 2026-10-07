# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_csv_activation`, rewritten on this harness: btclib-node.

`feature_csv_activation_test.py` beside this module holds the bodies, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared (`feature_dersig_btclib_node_test.py` has the measurement), and
every body asks for it, so each is a counted skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/feature_csv_activation_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_csv_activation_test import (
    csv_activates_one_block_before_the_configured_height,
    csv_rules_are_enforced_from_the_configured_height,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_csv_activates_one_block_before_the_configured_height(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    csv_activates_one_block_before_the_configured_height(
        btclib_node_cluster, skip_counts
    )


def test_csv_rules_are_enforced_from_the_configured_height(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    csv_rules_are_enforced_from_the_configured_height(btclib_node_cluster, skip_counts)
