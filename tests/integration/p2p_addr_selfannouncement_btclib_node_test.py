# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_addr_selfannouncement`, rewritten on this harness: btclib-node.

`p2p_addr_selfannouncement_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each body is a counted skip on every build:
`Capability.EXTERNAL_IP`, which every body asks for, is declared by none,
and neither are `Capability.KNOWN_ADDRESSES` nor
`Capability.TYPED_OUTBOUND` (`btclib_node.py`'s own docstring).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/p2p_addr_selfannouncement_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_addr_selfannouncement_test import (
    externalip_bypasses_onlynet,
    self_announcement_to_inbound_peers,
    self_announcement_to_inbound_peers_is_logged,
    self_announcement_to_outbound_peers,
    self_announcement_to_outbound_peers_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_self_announcement_to_inbound_peers(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    self_announcement_to_inbound_peers(btclib_node_cluster, skip_counts)


def test_self_announcement_to_inbound_peers_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    self_announcement_to_inbound_peers_is_logged(btclib_node_cluster, skip_counts)


def test_self_announcement_to_outbound_peers(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    self_announcement_to_outbound_peers(btclib_node_cluster, skip_counts)


def test_self_announcement_to_outbound_peers_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    self_announcement_to_outbound_peers_is_logged(btclib_node_cluster, skip_counts)


def test_externalip_bypasses_onlynet(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    externalip_bypasses_onlynet(btclib_node_cluster, skip_counts)
