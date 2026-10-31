# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_cltv`, rewritten on tf2's own harness: btcd.

`feature_cltv_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_cltv_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_cltv_test import (
    a_version_3_block_is_logged_once_active,
    a_version_3_block_is_refused_once_active,
    cltv_activates_one_block_before_the_configured_height,
    cltv_failures_are_mined_until_the_configured_height,
    cltv_failures_are_refused_by_the_mempool,
    cltv_failures_are_refused_in_a_block,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_cltv_activates_one_block_before_the_configured_height(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    cltv_activates_one_block_before_the_configured_height(btcd_cluster, skip_counts)


def test_a_version_3_block_is_refused_once_active(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    a_version_3_block_is_refused_once_active(btcd_cluster, skip_counts)


def test_a_version_3_block_is_logged_once_active(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    a_version_3_block_is_logged_once_active(btcd_cluster, skip_counts)


def test_cltv_failures_are_mined_until_the_configured_height(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    cltv_failures_are_mined_until_the_configured_height(btcd_cluster, skip_counts)


def test_cltv_failures_are_refused_by_the_mempool(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.ACCEPT_NON_STANDARD`."""
    cltv_failures_are_refused_by_the_mempool(btcd_cluster, skip_counts)


def test_cltv_failures_are_refused_in_a_block(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the block refusals, which ask for neither capability."""
    cltv_failures_are_refused_in_a_block(btcd_cluster, skip_counts)
