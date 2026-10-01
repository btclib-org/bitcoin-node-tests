# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_packages`, rewritten on tf2's own harness: btclib-node.

`mempool_packages_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test is a counted skip on every build, on
`Capability.MEMPOOL_GRAPH`, which neither build declares
([ISS btclib-node#1501](https://github.com/btclib-org/btclib-node/issues/1501)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_packages_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_packages_test import (
    mempool_tracks_ancestors_and_descendants,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mempool_tracks_ancestors_and_descendants(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mempool_tracks_ancestors_and_descendants(btclib_node_cluster, skip_counts)
