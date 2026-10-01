# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_permissions`, rewritten on tf2's own harness: btclib-node.

`p2p_permissions_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Every test is a counted skip on
`Capability.PEER_PERMISSIONS`, which `btclib_node.py`'s own docstring has
no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_permissions_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_permissions_test import (
    a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds,
    a_malformed_permission_list_stops_the_node_starting,
    a_whitebind_and_a_whitelist_grant_the_union,
    each_whitelist_grants_the_permissions_it_names,
    in_and_out_decide_which_connections_a_whitelist_grants,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
        btclib_node_cluster, skip_counts
    )


def test_a_malformed_permission_list_stops_the_node_starting(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_malformed_permission_list_stops_the_node_starting(
        btclib_node_cluster, skip_counts
    )


def test_a_whitebind_and_a_whitelist_grant_the_union(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_whitebind_and_a_whitelist_grant_the_union(btclib_node_cluster, skip_counts)


def test_each_whitelist_grants_the_permissions_it_names(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    each_whitelist_grants_the_permissions_it_names(btclib_node_cluster, skip_counts)


def test_in_and_out_decide_which_connections_a_whitelist_grants(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    in_and_out_decide_which_connections_a_whitelist_grants(
        btclib_node_cluster, skip_counts
    )
