# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--v2transport`, restated through the adapter: bitcoind.

Issue [bitcoin-node-tests#36](https://github.com/btclib-org/bitcoin-node-tests/issues/36):
this suite has no central test-framework object for Core's own
`--v2transport`/`--v1transport` to set a default on, so the equivalent is
`BitcoindAdapter`'s own `extra_args`, node by node -- the same mechanism
`feature_uacomment_bitcoind_test.py` already uses for `-uacomment`.
`getpeerinfo`'s own `transport_protocol_type` is what a real connection
answers with, measured live against the pinned `31.1` for both values of
the flag.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def _transport_protocol(adapter: BitcoindAdapter) -> str:
    """Return the one peer's own `transport_protocol_type`, or raise.

    :param adapter: a node with exactly one peer connected.
    :raises TypeError: `getpeerinfo` answered something other than the
        one-peer list this helper assumes.
    """
    peers = adapter.rpc.call("getpeerinfo")
    if not isinstance(peers, list) or len(peers) != 1:
        err_msg = f"getpeerinfo answered {peers!r}, not a one-peer list"
        raise TypeError(err_msg)
    protocol = peers[0]["transport_protocol_type"]
    if not isinstance(protocol, str):
        err_msg = f"transport_protocol_type was {protocol!r}, not a string"
        raise TypeError(err_msg)
    return protocol


def test_v2transport_1_connects_nodes_over_bip324(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """Explicit `-v2transport=1` on both sides: `getpeerinfo` answers `v2`."""
    first = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "first",
        free_port(),
        free_port(),
        extra_args=("-v2transport=1",),
    )
    second = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "second",
        free_port(),
        free_port(),
        extra_args=("-v2transport=1",),
    )
    require(Capability.V2TRANSPORT, first.capabilities, skip_counts)
    first.start()
    second.start()
    try:
        connect_nodes(first, second, v2transport=True)
        assert _transport_protocol(first) == "v2"
        assert _transport_protocol(second) == "v2"
    finally:
        second.stop()
        first.stop()


def test_v2transport_0_connects_nodes_over_v1(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """Explicit `-v2transport=0` on both sides: `getpeerinfo` answers `v1`."""
    first = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "first",
        free_port(),
        free_port(),
        extra_args=("-v2transport=0",),
    )
    second = BitcoindAdapter(
        bitcoind_path,
        tmp_path / "second",
        free_port(),
        free_port(),
        extra_args=("-v2transport=0",),
    )
    require(Capability.V2TRANSPORT, first.capabilities, skip_counts)
    first.start()
    second.start()
    try:
        connect_nodes(first, second)
        assert _transport_protocol(first) == "v1"
        assert _transport_protocol(second) == "v1"
    finally:
        second.stop()
        first.stop()
