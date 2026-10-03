# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--v2transport`, restated through the adapter: btclib-node.

`v2transport_option_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220): `Capability.V2TRANSPORT` is declared by a build
with btclib-node's `-v2transport` flag -- `btclib_node.py`'s own module
docstring has which -- so against a build without it, the PyPI release,
each counts a skip rather than a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/v2transport_option_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.v2transport_option_test import (
    v2transport_0_connects_nodes_over_v1,
    v2transport_1_connects_nodes_over_bip324,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_v2transport_1_connects_nodes_over_bip324(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    v2transport_1_connects_nodes_over_bip324(btclib_node_cluster, skip_counts)


def test_v2transport_0_connects_nodes_over_v1(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    v2transport_0_connects_nodes_over_v1(btclib_node_cluster, skip_counts)
