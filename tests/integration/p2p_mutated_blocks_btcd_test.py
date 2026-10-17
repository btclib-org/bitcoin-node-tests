# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_mutated_blocks`, rewritten on tf2's own harness: btcd.

`p2p_mutated_blocks_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_mutated_blocks_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_mutated_blocks_test import (
    block_missing_its_parent_drops_the_peer,
    block_missing_its_parent_is_logged,
    mutated_block_is_logged,
    mutated_block_keeps_the_honest_request,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mutated_block_keeps_the_honest_request(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mutated_block_keeps_the_honest_request(btcd_cluster, skip_counts)


def test_mutated_block_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    mutated_block_is_logged(btcd_cluster, skip_counts)


def test_block_missing_its_parent_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    block_missing_its_parent_drops_the_peer(btcd_cluster, skip_counts)


def test_block_missing_its_parent_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    block_missing_its_parent_is_logged(btcd_cluster, skip_counts)
