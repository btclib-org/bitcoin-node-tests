# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`FlorestadAdapter`: florestad, Floresta's utreexo node in Rust, on regtest.

The measurements below are of Floresta's `v0.9.1` release
(getfloresta/Floresta@bc2db8d), whose Homebrew bottle
`node-integration.yml`'s `florestad` job installs. This module holds no
fetch: it is handed the daemon's path, and `tests/integration/conftest.py`
is what hands it over.

`Capability.RPC_INFO` is declared: `getrpcinfo` names the calls running
and the path of `debug.log` (`crates/floresta-node/src/json_rpc/server.rs`).
florestad lacks what the others name, among them:

- florestad opens no p2p listener, so no peer can dial it
  (`crates/floresta-wire` binds none), and `p2p_port` is unused.
- It has no RPC that builds or submits a block.
- It downloads a block only from a peer serving utreexo proofs:
  `SyncNode`'s `maintenance_tick`
  (`crates/floresta-wire/src/p2p_wire/node/sync_ctx.rs`) requests none
  while it has no such peer. Beside a `bitcoind` that mines, it takes
  the headers offered at its first connection and validates none of
  their blocks; a block mined later did not reach it within 30 s.
  Measured against bitcoind 28.3. Its `getbestblockhash` and
  `getblockcount` answer that header chain.

florestad reads no credential: its RPC server has no authentication
layer. `bitcoin_core_rpc` sends one all the same, so the client is built
with `rpc_auth` where the caller names one, and otherwise with a user and
a password drawn per instance.

florestad writes nothing outside `--data-dir`: the home directory is
only its default data directory (`bin/florestad/src/main.rs`).
"""

from __future__ import annotations

import secrets
import signal
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter, free_port
from bitcoin_node_tests.timeout_factor import rpc_client_timeout

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "FlorestadAdapter",
]

# the user the client sends where the caller names no credential
_RPC_USER = "tf2"

# the subdirectory of `--data-dir` florestad writes into on regtest
# (`data_dir_path`, `bin/florestad/src/main.rs`)
_CHAIN_DIR = "regtest"


class FlorestadAdapter(NodeAdapter):
    """A `florestad`, its RPC and its Electrum server on loopback ports.

    The Electrum server cannot be turned off, and binds a fixed port per
    chain unless told otherwise, so each instance draws one with
    `node.free_port`.

    florestad prints its whole log to stdout, which `start` discards, and
    says why a start failed there and in `debug.log`, not on stderr: given
    an RPC port already taken, it exits 255 with stderr empty. That is the
    node `NodeAdapter._discards_stdout` is for.
    """

    capabilities: AbstractSet[Capability] = frozenset({Capability.RPC_INFO})
    _discards_stdout = True

    @override
    def __init__(
        self,
        executable: str,
        datadir: Path,
        rpc_port: int,
        p2p_port: int,
        extra_args: Sequence[str] = (),
        rpc_auth: tuple[str, str] | None = None,
        *,
        trace_rpc: bool = False,
        chain: str = "regtest",
    ) -> None:
        """Draw the Electrum port first: `_command` reads it.

        `NodeAdapter.__init__` calls `_command` to check `extra_args`.
        """
        self._electrum_port = free_port()
        self._credential = rpc_auth or (_RPC_USER, secrets.token_hex(16))
        super().__init__(
            executable,
            datadir,
            rpc_port,
            p2p_port,
            extra_args,
            rpc_auth,
            trace_rpc=trace_rpc,
            chain=chain,
        )

    @override
    def _command(self) -> list[str]:
        """Return florestad's own argv, a regtest node with no DNS seed.

        `--log-to-file` writes `debug.log`, which florestad otherwise prints
        to stdout alone. florestad refuses an option given twice ("an
        argument cannot be used with one or more of the other specified
        arguments"), so a short alias in `extra_args` cannot reset one of
        these.
        """
        return [
            self._executable,
            "--network",
            "regtest",
            "--data-dir",
            str(self._datadir),
            "--rpc-address",
            f"127.0.0.1:{self._rpc_port}",
            "--electrum-address",
            f"127.0.0.1:{self._electrum_port}",
            "--log-to-file",
            "--disable-dns-seeds",
        ]

    @override
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a client over this adapter's own connections.

        `NodeAdapter._rpc_transport`, `--tracerpc` included, and
        `timeout_factor.rpc_client_timeout`.
        """
        user, password = self._credential
        return BitcoinCoreRpcClient(
            f"http://127.0.0.1:{self._rpc_port}",
            user=user,
            password=password,
            timeout=rpc_client_timeout(),
            transport=self._rpc_transport(),
        )

    @override
    def _signal_stop(self, process: subprocess.Popen[bytes]) -> None:
        """Send SIGINT, the one signal florestad shuts down on.

        florestad waits for Ctrl-C alone (`bin/florestad/src/main.rs`), and
        SIGTERM kills it with no exit code of its own: measured, `-15`.
        """
        process.send_signal(signal.SIGINT)

    @property
    def log_path(self) -> Path:
        """Return this node's own `debug.log`."""
        return self._datadir / _CHAIN_DIR / "debug.log"

    @override
    def _log_path(self) -> Path:
        """Return `log_path`, for `start`'s own errors."""
        return self.log_path
