# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_1p1c_network`, rewritten on tf2's own harness: btclib-node.

`p2p_1p1c_network_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test asks first for `Capability.ORPHANAGE`,
which a build naming `getorphantxs` in its dispatch table declares, and
next for `Capability.PACKAGE_ACCEPTANCE`, which a build serving
`submitpackage` declares
([ISS btclib-node#1494](https://github.com/btclib-org/btclib-node/issues/1494)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_1p1c_network_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_1p1c_network_test import (
    every_node_takes_the_packages_one_node_is_given,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_every_node_takes_the_packages_one_node_is_given(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    every_node_takes_the_packages_one_node_is_given(btclib_node_cluster, skip_counts)
