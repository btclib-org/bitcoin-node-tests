# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_mutated_blocks`, rewritten on tf2's own harness: btclib-node.

`p2p_mutated_blocks_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The missing-parent wire half is a counted skip on
PyPI's `2026.9.24`, which declares no `Capability.MINE`, and passes on a
`main` past
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071).
Every other body is a counted skip on every build: the mutated-block
halves have the node dial the test, `Capability.TYPED_OUTBOUND` being
declared by none (`btclib_node.py`'s own docstring), and the
missing-parent log half asks for `Capability.TEST_ACTIVATION_HEIGHT` and
`Capability.DEBUG_LOG`, neither declared by any build.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_mutated_blocks_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mutated_block_keeps_the_honest_request(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mutated_block_keeps_the_honest_request(btclib_node_cluster, skip_counts)


def test_mutated_block_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mutated_block_is_logged(btclib_node_cluster, skip_counts)


def test_block_missing_its_parent_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    block_missing_its_parent_drops_the_peer(btclib_node_cluster, skip_counts)


def test_block_missing_its_parent_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    block_missing_its_parent_is_logged(btclib_node_cluster, skip_counts)
