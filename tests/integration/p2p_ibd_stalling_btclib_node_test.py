# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_ibd_stalling`, rewritten on tf2's own harness: btclib-node.

`p2p_ibd_stalling_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each body is a counted skip on every build: it
has the node dial the test, `Capability.TYPED_OUTBOUND` being declared by
none (`btclib_node.py`'s own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_ibd_stalling_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_ibd_stalling_test import (
    manual_peer_stalling_is_logged,
    manual_peer_stalling_pauses_the_peer,
    stalling_drops_the_staller,
    stalling_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_stalling_drops_the_staller(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    stalling_drops_the_staller(btclib_node_cluster, skip_counts)


def test_stalling_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    stalling_is_logged(btclib_node_cluster, skip_counts)


def test_manual_peer_stalling_pauses_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    manual_peer_stalling_pauses_the_peer(btclib_node_cluster, skip_counts)


def test_manual_peer_stalling_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    manual_peer_stalling_is_logged(btclib_node_cluster, skip_counts)
