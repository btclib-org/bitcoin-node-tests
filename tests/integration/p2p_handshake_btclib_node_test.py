# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`, rewritten on tf2's own harness: btclib-node.

`p2p_handshake_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
The wire half fails on PyPI's `2026.9.24`: `handle_p2p_handshake`
(`p2p/main.py`) discourages and stops a `verack` arriving once the
connection is already `Connected`
([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)).
A `main` past that issue ignores it, as Core does. The log half is a counted
skip on every build, `Capability.DEBUG_LOG` being bitcoind's alone. Every
other body has the node dial the test, and is a counted skip on every build
too, `Capability.TYPED_OUTBOUND` being declared by none (`btclib_node.py`'s
own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_handshake_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_handshake_test import (
    feeler_completion_is_logged,
    feeler_is_dropped_after_its_version,
    limited_peer_is_kept_only_near_the_tip,
    limited_peer_refusal_is_logged,
    outbound_services_decide_the_connection,
    outbound_services_refusal_is_logged,
    redundant_verack_is_logged,
    redundant_verack_keeps_the_connection,
    self_connection_is_dropped,
    self_connection_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_redundant_verack_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build (ISS btclib-node#1133)."""
    redundant_verack_keeps_the_connection(btclib_node_adapter)


def test_redundant_verack_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    redundant_verack_is_logged(btclib_node_adapter, skip_counts)


def test_outbound_services_decide_the_connection(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    outbound_services_decide_the_connection(btclib_node_cluster, skip_counts)


def test_outbound_services_refusal_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    outbound_services_refusal_is_logged(btclib_node_cluster, skip_counts)


def test_limited_peer_is_kept_only_near_the_tip(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    limited_peer_is_kept_only_near_the_tip(btclib_node_cluster, skip_counts)


def test_limited_peer_refusal_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    limited_peer_refusal_is_logged(btclib_node_cluster, skip_counts)


def test_feeler_is_dropped_after_its_version(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    feeler_is_dropped_after_its_version(btclib_node_cluster, skip_counts)


def test_feeler_completion_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    feeler_completion_is_logged(btclib_node_cluster, skip_counts)


def test_self_connection_is_dropped(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    self_connection_is_dropped(btclib_node_cluster, skip_counts)


def test_self_connection_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    self_connection_is_logged(btclib_node_cluster, skip_counts)
