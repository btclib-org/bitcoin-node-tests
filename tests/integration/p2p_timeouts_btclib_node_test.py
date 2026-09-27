# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_timeouts`, rewritten on this harness: btclib-node.

`p2p_timeouts_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Every test is a counted skip on
`Capability.PEER_TIMEOUT`, which `btclib_node.py`'s own docstring has
no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_timeouts_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_timeouts_test import (
    a_non_positive_peertimeout_is_refused,
    handshake_timeouts_are_logged,
    peers_that_never_finish_the_handshake_are_dropped,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_peers_that_never_finish_the_handshake_are_dropped(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    peers_that_never_finish_the_handshake_are_dropped(btclib_node_cluster, skip_counts)


def test_handshake_timeouts_are_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    handshake_timeouts_are_logged(btclib_node_cluster, skip_counts)


def test_a_non_positive_peertimeout_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the refused start the body module names, over btclib-node."""
    a_non_positive_peertimeout_is_refused(btclib_node_cluster, skip_counts)
