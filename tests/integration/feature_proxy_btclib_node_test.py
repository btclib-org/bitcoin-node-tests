# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, rewritten on this harness: btclib-node.

`feature_proxy_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Every test is a counted skip on
`Capability.PROXY`: `-proxy` is not one of `cli.py`'s own registered
flags, on the released build or on `main` (`btclib_node.py`'s own
docstring has the measurement).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_proxy_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_proxy_test import (
    onion_reaches_tor_through_a_proxy_of_its_own,
    proxy_reaches_every_network_through_one_proxy,
    proxyrandomize_gives_each_connection_credentials_of_its_own,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_proxy_reaches_every_network_through_one_proxy(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    proxy_reaches_every_network_through_one_proxy(btclib_node_cluster, skip_counts)


def test_onion_reaches_tor_through_a_proxy_of_its_own(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    onion_reaches_tor_through_a_proxy_of_its_own(btclib_node_cluster, skip_counts)


def test_proxyrandomize_gives_each_connection_credentials_of_its_own(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    proxyrandomize_gives_each_connection_credentials_of_its_own(
        btclib_node_cluster, skip_counts
    )
