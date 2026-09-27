# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_cltv`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_cltv.py`: `feature_cltv_test.py`
beside this module holds the bodies, run here against bitcoind.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_cltv_activates_one_block_before_the_configured_height(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `getdeploymentinfo`'s own `bip65` entry."""
    cltv_activates_one_block_before_the_configured_height(bitcoind_cluster, skip_counts)


def test_a_version_3_block_is_refused_once_active(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `submitblock`'s own `bad-version(0x00000003)`."""
    a_version_3_block_is_refused_once_active(bitcoind_cluster, skip_counts)


def test_a_version_3_block_is_logged_once_active(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the same refusal in its own debug log."""
    a_version_3_block_is_logged_once_active(bitcoind_cluster, skip_counts)


def test_cltv_failures_are_mined_until_the_configured_height(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: CLTV failures mined before the height, refused at it."""
    cltv_failures_are_mined_until_the_configured_height(bitcoind_cluster, skip_counts)


def test_cltv_failures_are_refused_by_the_mempool(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `testmempoolaccept`'s own reason for each CLTV failure."""
    cltv_failures_are_refused_by_the_mempool(bitcoind_cluster, skip_counts)


def test_cltv_failures_are_refused_in_a_block(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `submitblock`'s own reason for each CLTV failure."""
    cltv_failures_are_refused_in_a_block(bitcoind_cluster, skip_counts)
