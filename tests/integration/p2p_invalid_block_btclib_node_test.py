# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_block`, rewritten on tf2's own harness: btclib-node.

`p2p_invalid_block_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each test is a counted skip on every build: on
PyPI's `2026.9.24`, which declares no `Capability.MINE`, and on a `main`
past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
on `Capability.CLOCK`, which no build declares (`btclib_node.py`'s own
docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_invalid_block_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_invalid_block_test import (
    invalid_blocks_are_logged,
    invalid_blocks_are_refused,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_invalid_blocks_are_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    invalid_blocks_are_refused(btclib_node_cluster, skip_counts)


def test_invalid_blocks_are_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    invalid_blocks_are_logged(btclib_node_cluster, skip_counts)
