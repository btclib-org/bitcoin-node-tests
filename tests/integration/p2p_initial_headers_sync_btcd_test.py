# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_initial_headers_sync`, on tf2's own harness: btcd.

`p2p_initial_headers_sync_test.py` beside this module is the body, run
here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_initial_headers_sync_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_initial_headers_sync_test import (
    headers_are_asked_of_one_peer_per_announcement,
    headers_timeout_drops_the_peer,
    headers_timeout_is_logged,
    headers_timeout_keeps_a_noban_peer,
    headers_timeout_of_a_noban_peer_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_headers_are_asked_of_one_peer_per_announcement(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
) -> None:
    """The target: fails on the release, the module docstring having why."""
    headers_are_asked_of_one_peer_per_announcement(btcd_cluster)


def test_headers_timeout_drops_the_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    headers_timeout_drops_the_peer(btcd_cluster, skip_counts)


def test_headers_timeout_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    headers_timeout_is_logged(btcd_cluster, skip_counts)


def test_headers_timeout_keeps_a_noban_peer(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    headers_timeout_keeps_a_noban_peer(btcd_cluster, skip_counts)


def test_headers_timeout_of_a_noban_peer_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    headers_timeout_of_a_noban_peer_is_logged(btcd_cluster, skip_counts)
