# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_eviction`, rewritten on this harness: btclib-node.

`p2p_eviction_test.py` beside this module holds the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.INBOUND_EVICTION` and
`Capability.MINE` are declared per build (`btclib_node.py`'s own
docstring): a build without either is a counted skip before any peer
connects. The node's `-help` is read with `-noconf`, keeping any
`bitcoin.conf` out of it; btclib-node refuses `-nosettings`, the flag
the bitcoind module passes.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_eviction_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_eviction_test import (
    the_evicted_inbound_peer_is_never_a_protected_one,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_the_evicted_inbound_peer_is_never_a_protected_one(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    btclib_node_python: str,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    the_evicted_inbound_peer_is_never_a_protected_one(
        btclib_node_cluster,
        (btclib_node_python, "-m", "btclib_node", "-help", "-noconf"),
        skip_counts,
    )
