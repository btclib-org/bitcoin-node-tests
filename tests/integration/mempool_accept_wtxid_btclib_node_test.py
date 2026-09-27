# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_accept_wtxid`, rewritten on tf2's own harness: btclib-node.

`mempool_accept_wtxid_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). It asks for `Capability.MINE` alone, which a
build declares per instance (`btclib_node.py`'s own docstring is how).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_accept_wtxid_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_accept_wtxid_test import (
    a_child_sharing_a_txid_is_told_apart_by_its_wtxid,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_child_sharing_a_txid_is_told_apart_by_its_wtxid(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_child_sharing_a_txid_is_told_apart_by_its_wtxid(btclib_node_cluster, skip_counts)
