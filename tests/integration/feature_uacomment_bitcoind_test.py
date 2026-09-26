# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_uacomment`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_uacomment.py` (`fa5f29774872`,
2025-12-16) and ported in part, the first test of the option family
(rule 4 of issue btclib-org/btclib#2220,
[ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)):
`-uacomment` appends a comment to the subversion string
`getnetworkinfo` reports. No other step-5 mechanism is asked for, nor
`Capability.MINE` nor an outbound connection.

A smaller claim than Core's own test, declared rather than silent:
Core's own harness sets `-uacomment=testnode{i}` on every node it
starts and asserts a second comment is appended alongside that one on
restart; this adapter sets no default comment, so the claim kept is
that one appears once named, against a node carrying none by default,
rather than that a second one joins a first. The length-limit and
unsafe-character checks are dropped too: both ask a node to refuse to
start on a bad value, which is a fact about a rejected argument, not
about this capability.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_uacomment_appends_to_the_subversion_string(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A comment appears in `getnetworkinfo`'s subversion once named."""
    rpc_port1, p2p_port1 = free_ports(2)
    plain = make_adapter(
        BitcoindAdapter, bitcoind_path, tmp_path / "plain", rpc_port1, p2p_port1
    )
    plain.start()
    try:
        require(Capability.UA_COMMENT, plain.capabilities, skip_counts)
        assert "(" not in plain.rpc.call("getnetworkinfo")["subversion"]
    finally:
        plain.stop()

    rpc_port2, p2p_port2 = free_ports(2)
    commented = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path / "commented",
        rpc_port2,
        p2p_port2,
        extra_args=("-uacomment=foo",),
    )
    commented.start()
    try:
        assert "(foo)" in commented.rpc.call("getnetworkinfo")["subversion"]
    finally:
        commented.stop()
