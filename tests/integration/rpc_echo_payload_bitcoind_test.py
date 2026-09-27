# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_echo_payload`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_echo_payload.py` (`fa7bc26d1276`,
2026-08-06), an option-family row
([ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)):
a node started with `-rpcworkqueue=2` and `-rpcthreads=2`
(`Capability.RPC_WORK_QUEUE`) takes payloads of random length, large
ones included, from more concurrent callers than its threads and its
queue hold, each payload sent through `echo` or `sendrawtransaction`
chosen at random, and answers or refuses every request rather than
leaving one to time out: a timeout is `bitcoin_core_rpc`'s own
`FetchError`, which neither `except` clause of `_call_repeatedly`
catches.

A smaller claim than Core's own test, declared rather than silent: Core
matches a refusal on its message, "Work queue depth exceeded" after the
HTTP 503 status, where `bitcoin_core_rpc`'s own `HttpError` carries the
status alone, the body of a non-JSON reply not being kept, so a refusal
here is the 503 status. Each caller's client opens a connection per call
rather than holding one open, `urlopen_transport` being the transport
`BitcoindAdapter` builds; up to `_CALLERS` requests are still in
flight at once, as in Core's own.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import HttpError, RpcError

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# Core's own `set_test_params`: enough callers to fill both worker threads
# and the queue behind them
_CALLERS = 6
_CALLS_PER_CALLER = 200

# `sendrawtransaction`'s own answer to a payload that is no transaction
_DECODE_FAILED = "TX decode failed. Make sure the tx has at least one input."

# the status `src/httpserver.cpp` refuses a request with once the queue is full
_SERVICE_UNAVAILABLE = 503


def _call_repeatedly(node: BitcoindAdapter, data: str) -> None:
    """Send random prefixes of `data`, accepting an answer or a refusal only."""
    for _ in range(_CALLS_PER_CALLER):
        payload = data[: random.randrange(len(data))]
        try:
            if random.getrandbits(1):
                assert node.rpc.call("echo", [payload]) == [payload]
            else:
                node.rpc.call("sendrawtransaction", [payload])
        except RpcError as e:
            if _DECODE_FAILED not in str(e):
                raise
        except HttpError as e:
            if e.status != _SERVICE_UNAVAILABLE:
                raise


def test_a_payload_is_answered_or_refused_never_left_to_time_out(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Core's own subject: every request is answered or refused in time."""
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path / "node",
        rpc_port,
        p2p_port,
        extra_args=("-rpcworkqueue=2", "-rpcthreads=2"),
    )
    require(Capability.RPC_WORK_QUEUE, node.capabilities, skip_counts)
    # json-serializable, but not hex
    data = "z" + random.randbytes(1_999_000).hex()
    node.start()
    try:
        with ThreadPoolExecutor(max_workers=_CALLERS) as callers:
            futures = [
                callers.submit(_call_repeatedly, node, data) for _ in range(_CALLERS)
            ]
        for future in futures:
            future.result()
    finally:
        node.stop()
