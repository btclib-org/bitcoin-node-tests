# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_scanblocks`, rewritten on tf2's own harness: btcd.

`rpc_scanblocks_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_scanblocks_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_scanblocks_test import (
    scanblocks_finds_the_blocks_paying_what_it_is_asked_for,
    scanblocks_refuses_without_the_index,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_scanblocks_finds_the_blocks_paying_what_it_is_asked_for(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the scans the body module names, over btcd."""
    scanblocks_finds_the_blocks_paying_what_it_is_asked_for(btcd_cluster, skip_counts)


def test_scanblocks_refuses_without_the_index(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the refusal the body module names, over btcd."""
    scanblocks_refuses_without_the_index(btcd_cluster, skip_counts)
