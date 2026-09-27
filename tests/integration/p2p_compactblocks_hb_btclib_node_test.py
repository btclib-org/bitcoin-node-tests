# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_compactblocks_hb`, rewritten on tf2's own harness: btclib-node.

`p2p_compactblocks_hb_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.MINE` is declared only by a build
that connects a submitted block with no peer (`btclib_node.py`'s own
docstring): PyPI's `2026.9.24` is a counted skip here. A `main` from
btclib-node PR 1152 on declares it and is a counted skip on
`Capability.DISCONNECT` instead, `btclib_node.py`'s own docstring
measuring neither build answering `disconnectnode`
([ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_compactblocks_hb_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_compactblocks_hb_test import (
    reserved_high_bandwidth_slot_for_the_outbound_peer,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_reserved_high_bandwidth_slot_for_the_outbound_peer(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    reserved_high_bandwidth_slot_for_the_outbound_peer(btclib_node_cluster, skip_counts)
