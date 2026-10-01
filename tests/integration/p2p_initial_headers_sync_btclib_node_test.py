# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_initial_headers_sync`, on tf2's own harness: btclib-node.

`p2p_initial_headers_sync_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The first check dials the node alone and asks
for no capability, and fails on the released build. PyPI's `2026.9.24` sends
every peer a `getheaders` at its `verack`, where Core asks one peer until
its best header is recent; the change closing
[ISS btclib-node#1073](https://github.com/btclib-org/btclib-node/issues/1073)
leaves that to `DownloadManager.sync_headers`, and a `main` past it
passes, though `Connection.parse_messages` queues a `ping` ahead of
messages its peer sent before it
([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410)).
Every timeout check has the node dial the test, and is a counted skip on
every build, `Capability.TYPED_OUTBOUND` being declared by none
(`btclib_node.py`'s own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_initial_headers_sync_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_headers_are_asked_of_one_peer_per_announcement(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: fails on the release, the module docstring having why."""
    headers_are_asked_of_one_peer_per_announcement(btclib_node_cluster)


def test_headers_timeout_drops_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    headers_timeout_drops_the_peer(btclib_node_cluster, skip_counts)


def test_headers_timeout_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    headers_timeout_is_logged(btclib_node_cluster, skip_counts)


def test_headers_timeout_keeps_a_noban_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    headers_timeout_keeps_a_noban_peer(btclib_node_cluster, skip_counts)


def test_headers_timeout_of_a_noban_peer_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    headers_timeout_of_a_noban_peer_is_logged(btclib_node_cluster, skip_counts)
