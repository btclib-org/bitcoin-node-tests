# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_eviction`, rewritten on this harness: btclib-node.

The same request `p2p_eviction_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.INBOUND_EVICTION` is checked against a constructed
instance's own `capabilities`, never the class's: `btclib_node.py`'s own
docstring is where its per-executable probe is argued, and constructing
an adapter spawns nothing. PyPI's `2026.9.24` release lacks it, a
counted skip on that capability; a `main` past
[ISS btclib-node#1064](https://github.com/btclib-org/btclib-node/issues/1064)
declares it and asks for `Capability.MINE` next, the blocks and the
transactions the protected peers send being mined first; a `main` from
btclib-node PR 1152 on declares that too (`btclib_node.py`'s own
docstring) and reaches this stub's own `pytest.fail`, the scenario not
being ported yet.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_eviction_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_the_evicted_inbound_peer_is_never_a_protected_one(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the same request the bitcoind module makes."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, tmp_path, rpc_port, p2p_port
    )
    require(Capability.INBOUND_EVICTION, adapter.capabilities, skip_counts)
    require(Capability.MINE, adapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
