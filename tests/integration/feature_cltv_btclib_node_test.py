# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_cltv`, rewritten on this harness: btclib-node.

`feature_cltv_test.py` beside this module holds the bodies, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared (`TF2.md`'s activation-trio paragraph has the measurement), nor
is `Capability.ACCEPT_NON_STANDARD` (`btclib_node.py`'s own docstring
has it), so every body asking for either is a counted skip; the block
refusals ask for neither.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_cltv_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_cltv_activates_one_block_before_the_configured_height(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    cltv_activates_one_block_before_the_configured_height(
        btclib_node_cluster, skip_counts
    )


def test_a_version_3_block_is_refused_once_active(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    a_version_3_block_is_refused_once_active(btclib_node_cluster, skip_counts)


def test_a_version_3_block_is_logged_once_active(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    a_version_3_block_is_logged_once_active(btclib_node_cluster, skip_counts)


def test_cltv_failures_are_mined_until_the_configured_height(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.TEST_ACTIVATION_HEIGHT`."""
    cltv_failures_are_mined_until_the_configured_height(
        btclib_node_cluster, skip_counts
    )


def test_cltv_failures_are_refused_by_the_mempool(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: skipped on `Capability.ACCEPT_NON_STANDARD`."""
    cltv_failures_are_refused_by_the_mempool(btclib_node_cluster, skip_counts)


def test_cltv_failures_are_refused_in_a_block(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the block refusals, which ask for neither capability."""
    cltv_failures_are_refused_in_a_block(btclib_node_cluster, skip_counts)
