# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_permissions`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/p2p_permissions.py`:
`p2p_permissions_test.py` beside this module holds each body, run here
against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
        bitcoind_cluster, skip_counts
    )


def test_a_malformed_permission_list_stops_the_node_starting(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_malformed_permission_list_stops_the_node_starting(bitcoind_cluster, skip_counts)


def test_a_whitebind_and_a_whitelist_grant_the_union(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_whitebind_and_a_whitelist_grant_the_union(bitcoind_cluster, skip_counts)


def test_each_whitelist_grants_the_permissions_it_names(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    each_whitelist_grants_the_permissions_it_names(bitcoind_cluster, skip_counts)


def test_in_and_out_decide_which_connections_a_whitelist_grants(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    in_and_out_decide_which_connections_a_whitelist_grants(
        bitcoind_cluster, skip_counts
    )
