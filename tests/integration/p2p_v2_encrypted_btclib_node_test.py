# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_v2_encrypted`: btclib-node.

`p2p_v2_encrypted_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each body skips on a build that does not
declare the capabilities it asks for: `Capability.V2TRANSPORT` for both,
`Capability.CONNECT` and `Capability.DISCONNECT` for the inbound body,
and `Capability.TYPED_OUTBOUND` for the outbound one.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_v2_encrypted_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_v2_encrypted_test import (
    inbound_connections_and_blocks,
    outbound_connections,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_inbound_connections_and_blocks(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    inbound_connections_and_blocks(btclib_node_cluster, skip_counts)


def test_outbound_connections(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    outbound_connections(btclib_node_cluster, skip_counts)
