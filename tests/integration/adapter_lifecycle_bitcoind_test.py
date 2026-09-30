# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: bitcoind.

What `tests/node_test.py` and `tests/bitcoind_test.py` fake, run against
the process itself: `mine` after a `restart` and over a datadir an
earlier adapter left
([ISS 86](https://github.com/btclib-org/bitcoin-node-tests/issues/86)),
`stop` reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84)),
and a kept RPC connection still open after idling past bitcoind's default
`-rpcservertimeout`
([ISS 336](https://github.com/btclib-org/bitcoin-node-tests/issues/336)).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import os
import signal
import time
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import transport

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# `DEFAULT_HTTP_SERVER_TIMEOUT` (`src/httpserver.h`), 30 s, with a margin
_PAST_DEFAULT_SERVER_TIMEOUT = 35


def _adapter(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    datadir: Path,
    skip_counts: SkipCounts,
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(BitcoindAdapter, bitcoind_path, datadir, rpc_port, p2p_port)
    require(Capability.MINE, adapter.capabilities, skip_counts)
    return adapter


def test_mine_after_restart(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A restart unloads the wallet `mine` pays to; `mine` loads it back."""
    adapter = _adapter(make_adapter, bitcoind_path, tmp_path / "node", skip_counts)
    adapter.start()
    try:
        adapter.mine(1)
        adapter.restart()
        adapter.mine(1)
        assert adapter.rpc.call("getblockcount") == 2
    finally:
        adapter.stop()


def test_mine_over_a_datadir_an_earlier_adapter_left(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A second adapter over the same datadir mines to the wallet on disk."""
    datadir = tmp_path / "node"
    first = _adapter(make_adapter, bitcoind_path, datadir, skip_counts)
    first.start()
    try:
        first.mine(1)
    finally:
        first.stop()
    second = _adapter(make_adapter, bitcoind_path, datadir, skip_counts)
    second.start()
    try:
        second.mine(1)
        assert second.rpc.call("getblockcount") == 2
    finally:
        second.stop()


def test_stop_reports_a_node_killed_out_from_under_it(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> None:
    """A node gone before `stop` is raised, and nothing is left to stop."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter, bitcoind_path, tmp_path / "node", rpc_port, p2p_port
    )
    adapter.start()
    running = adapter._running
    process = None if running is None else running.process
    try:
        assert process is not None
        os.kill(process.pid, signal.SIGKILL)
        process.wait()
        with pytest.raises(
            RuntimeError, match=r"^node process exited with -9 before stop was called"
        ):
            adapter.stop()
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
    adapter.stop()


def test_a_kept_connection_outlives_the_default_server_timeout(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A connection idle past bitcoind's default server timeout is still open.

    `SessionTransport` probes a kept connection before reusing it, and
    replaces one the probe finds closed, so an answered call alone cannot
    tell a connection the server kept from one it closed. The probe here
    records what the real one answers and then answers `False` regardless,
    which is what a server's idle close landing between that probe and the
    request looks like to the transport: the one probe the call after the
    idle makes has to have found the connection open. `start` leaves the
    connection its own polling opened pooled, and the answers that polling
    recorded are cleared before the idle.
    """
    real_probe = transport._is_reused_connection_dead
    probed: list[bool] = []

    def recording_probe(connection: transport._Connection) -> bool:
        probed.append(real_probe(connection))
        return False

    monkeypatch.setattr(transport, "_is_reused_connection_dead", recording_probe)
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter, bitcoind_path, tmp_path / "node", rpc_port, p2p_port
    )
    adapter.start()
    try:
        probed.clear()
        time.sleep(_PAST_DEFAULT_SERVER_TIMEOUT)
        assert adapter.rpc.call("getblockcount") == 0
        assert probed == [False]
    finally:
        adapter.stop()
