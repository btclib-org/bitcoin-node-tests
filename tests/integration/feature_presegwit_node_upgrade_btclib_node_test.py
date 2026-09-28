# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_presegwit_node_upgrade`, rewritten here: btclib-node.

`feature_presegwit_node_upgrade_test.py` beside this module is the body,
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared: `-testactivationheight` is not one of `cli.py`'s own
registered flags, the measurement `feature_dersig_btclib_node_test.py`'s
own docstring already names -- a counted skip on that capability alone,
before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/feature_presegwit_node_upgrade_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_presegwit_node_upgrade_test import (
    a_pre_segwit_chain_needs_a_reindex_to_upgrade,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_pre_segwit_chain_needs_a_reindex_to_upgrade(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_pre_segwit_chain_needs_a_reindex_to_upgrade(btclib_node_cluster, skip_counts)
