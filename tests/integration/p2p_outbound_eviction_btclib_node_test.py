# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_outbound_eviction`, rewritten on tf2's own harness: btclib-node.

`p2p_outbound_eviction_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each body has the node dial the test, and
`Capability.TYPED_OUTBOUND` is declared by no build (`btclib_node.py`'s
own docstring,
[ISS btclib-node#1465](https://github.com/btclib-org/btclib-node/issues/1465)),
so each test is a counted skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_outbound_eviction_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_outbound_eviction_test import (
    block_relay_only_peer_is_not_protected,
    lagging_unprotected_peers_are_evicted,
    only_misbehaving_unprotected_peers_are_evicted,
    protected_peer_is_not_evicted,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_lagging_unprotected_peers_are_evicted(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    lagging_unprotected_peers_are_evicted(btclib_node_cluster, skip_counts)


def test_protected_peer_is_not_evicted(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    protected_peer_is_not_evicted(btclib_node_cluster, skip_counts)


def test_only_misbehaving_unprotected_peers_are_evicted(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    only_misbehaving_unprotected_peers_are_evicted(btclib_node_cluster, skip_counts)


def test_block_relay_only_peer_is_not_protected(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    block_relay_only_peer_is_not_protected(btclib_node_cluster, skip_counts)
