# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_permissions`, rewritten on tf2's own harness: btcd.

`p2p_permissions_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_permissions_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
        btcd_cluster, skip_counts
    )


def test_a_malformed_permission_list_stops_the_node_starting(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_malformed_permission_list_stops_the_node_starting(btcd_cluster, skip_counts)


def test_a_whitebind_and_a_whitelist_grant_the_union(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_whitebind_and_a_whitelist_grant_the_union(btcd_cluster, skip_counts)


def test_each_whitelist_grants_the_permissions_it_names(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    each_whitelist_grants_the_permissions_it_names(btcd_cluster, skip_counts)


def test_in_and_out_decide_which_connections_a_whitelist_grants(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    in_and_out_decide_which_connections_a_whitelist_grants(btcd_cluster, skip_counts)
