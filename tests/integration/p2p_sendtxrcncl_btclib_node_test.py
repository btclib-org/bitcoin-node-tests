# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_sendtxrcncl`, rewritten on tf2's own harness: btclib-node.

`p2p_sendtxrcncl_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The check without `-txreconciliation` asks for
no capability. Every other body is a counted skip on every build,
`Capability.TX_RECONCILIATION` being declared by none, and the log half
of the check without the option on `Capability.DEBUG_LOG`
(`btclib_node.py`'s own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_sendtxrcncl_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_sendtxrcncl_test import (
    sendtxrcncl_is_ignored_without_the_option,
    sendtxrcncl_is_ignored_without_the_option_in_the_log,
    sendtxrcncl_is_not_sent_in_blocks_only_mode,
    sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay,
    sendtxrcncl_is_sent_to_full_relay_outbound_peers,
    sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions,
    sendtxrcncl_kept_peers_are_logged,
    sendtxrcncl_kept_peers_stay_connected,
    sendtxrcncl_on_block_relay_only_is_logged,
    sendtxrcncl_violations_are_logged,
    sendtxrcncl_violations_drop_the_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_sent_to_inbound_peers_relaying_transactions(
        btclib_node_cluster, skip_counts
    )


def test_sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_not_sent_with_bloom_filters_and_no_relay(
        btclib_node_cluster, skip_counts
    )


def test_sendtxrcncl_is_sent_to_full_relay_outbound_peers(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_sent_to_full_relay_outbound_peers(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_on_block_relay_only_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_on_block_relay_only_is_logged(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_is_not_sent_in_blocks_only_mode(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_not_sent_in_blocks_only_mode(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_is_ignored_without_the_option(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_ignored_without_the_option(btclib_node_cluster)


def test_sendtxrcncl_is_ignored_without_the_option_in_the_log(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_is_ignored_without_the_option_in_the_log(
        btclib_node_cluster, skip_counts
    )


def test_sendtxrcncl_violations_drop_the_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_violations_drop_the_peer(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_violations_are_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_violations_are_logged(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_stay_connected(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_kept_peers_stay_connected(btclib_node_cluster, skip_counts)


def test_sendtxrcncl_kept_peers_are_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    sendtxrcncl_kept_peers_are_logged(btclib_node_cluster, skip_counts)
