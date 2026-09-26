# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_net_deadlock`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_net_deadlock.py` (`a0473442d1c2`,
2024-07-16): two connected nodes each send the other a four-megabyte
message of an unrecognised command, at the same time, over `sendmsgtopeer`
-- a debug RPC that puts an arbitrary message on the wire on the node's
own behalf, so this asks for a full-duplex send with neither side reading
in between rather than something either adapter's own p2p codec builds.
`Capability.RAW_MESSAGE` names it, and only bitcoind offers it today.
Liveness afterwards is the whole check: Core's own `run_test` mines and
calls `sync_blocks`, neither node being expected to answer differently
had the sends deadlocked -- a hung network thread is what this would
catch, not a wrong reply.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import connect_nodes, wait_until_tips_agree
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own size: large enough that a socket's send buffer fills before
# the other side has read any of it, which is the condition a deadlock
# needs
_MESSAGE_SIZE = 4_000_000


def test_simultaneous_large_messages_do_not_deadlock(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: both sides survive sending at the same time."""
    node0, node1 = bitcoind_cluster(2)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.RAW_MESSAGE, node0.capabilities, skip_counts)
    require(Capability.MINE, node0.capabilities, skip_counts)

    connect_nodes(node1, node0)

    message = secrets.token_bytes(_MESSAGE_SIZE).hex()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(node0.rpc.call, "sendmsgtopeer", [0, "unknown", message]),
            executor.submit(node1.rpc.call, "sendmsgtopeer", [0, "unknown", message]),
        ]
        for future in futures:
            future.result(timeout=scaled(60.0))

    node0.mine(1)
    wait_until_tips_agree([node0, node1])
