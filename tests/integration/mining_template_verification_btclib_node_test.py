# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mining_template_verification`, on this harness: btclib-node.

`mining_template_verification_test.py` beside this module is the body,
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.BLOCK_PROPOSAL` is not declared
(`btclib_node.py`'s own docstring is why), so each is a counted skip
ahead of `Capability.MINE`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mining_template_*_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mining_template_verification_test import (
    a_proposed_block_is_checked_and_not_stored,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_proposed_block_is_checked_and_not_stored(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_proposed_block_is_checked_and_not_stored(btclib_node_cluster, skip_counts)
