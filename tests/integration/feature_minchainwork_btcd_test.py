# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_minchainwork`, rewritten on tf2's own harness: btcd.

`feature_minchainwork_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_minchainwork_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_minchainwork_test import (
    block_relay_waits_for_the_minimum_chain_work,
    outbound_peers_with_too_little_work_are_dropped_in_ibd,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_block_relay_waits_for_the_minimum_chain_work(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    block_relay_waits_for_the_minimum_chain_work(btcd_cluster, skip_counts)


def test_outbound_peers_with_too_little_work_are_dropped_in_ibd(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    outbound_peers_with_too_little_work_are_dropped_in_ibd(btcd_cluster, skip_counts)
