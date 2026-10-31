# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_csv_activation`, rewritten on tf2's own harness: btcd.

`feature_csv_activation_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_csv_activation_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_csv_activates_one_block_before_the_configured_height(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    csv_activates_one_block_before_the_configured_height(btcd_cluster, skip_counts)


def test_csv_rules_are_enforced_from_the_configured_height(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    csv_rules_are_enforced_from_the_configured_height(btcd_cluster, skip_counts)
