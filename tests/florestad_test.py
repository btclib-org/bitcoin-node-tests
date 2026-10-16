# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`FlorestadAdapter`'s own command line, RPC client and stop signal."""

from __future__ import annotations

import signal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.florestad import FlorestadAdapter
from bitcoin_node_tests.timeout_factor import set_factor

if TYPE_CHECKING:
    from pathlib import Path


def test_capabilities_are_the_ones_florestad_answers() -> None:
    """The class declares what `florestad.py`'s own docstring measures."""
    assert FlorestadAdapter.capabilities == frozenset({Capability.RPC_INFO})


def test_command_runs_florestad_on_regtest_over_loopback(tmp_path: Path) -> None:
    """Every option names the instance's own datadir and ports."""
    adapter = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    assert adapter._command() == [
        "florestad",
        "--network",
        "regtest",
        "--data-dir",
        str(tmp_path),
        "--rpc-address",
        "127.0.0.1:18443",
        "--electrum-address",
        f"127.0.0.1:{adapter._electrum_port}",
        "--log-to-file",
        "--disable-dns-seeds",
    ]


def test_each_instance_draws_its_own_electrum_port(tmp_path: Path) -> None:
    """Two instances never share the Electrum server's port."""
    first = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    second = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    assert first._electrum_port != second._electrum_port


def test_init_refuses_extra_args_naming_an_option_of_the_command(
    tmp_path: Path,
) -> None:
    """`--data-dir`, set by `_command`, is refused rather than reused."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -data-dir\b"):
        FlorestadAdapter(
            "florestad", tmp_path, 18443, 18444, extra_args=["--data-dir=x"]
        )


def test_init_refuses_a_chain_other_than_regtest(tmp_path: Path) -> None:
    """Regtest is the one chain this adapter starts."""
    with pytest.raises(ValueError, match="cannot start a node on chain 'signet'"):
        FlorestadAdapter("florestad", tmp_path, 18443, 18444, chain="signet")


def test_stdout_is_discarded() -> None:
    """Florestad prints its log to stdout as well as to `debug.log`."""
    assert FlorestadAdapter._discards_stdout


def test_rpc_client_sends_rpc_auth_where_given(tmp_path: Path) -> None:
    """The client's user and url are the caller's and the instance's."""
    adapter = FlorestadAdapter(
        "florestad", tmp_path, 18443, 18444, rpc_auth=("bob", "pw")
    )
    client = adapter._rpc_client()
    assert client.user == "bob"
    assert client.url == "http://127.0.0.1:18443"


def test_rpc_client_draws_a_credential_without_rpc_auth(tmp_path: Path) -> None:
    """Without `rpc_auth`, the client still sends a user: it needs one."""
    adapter = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    assert adapter._rpc_client().user == "tf2"


def test_rpc_client_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """A call is bounded by the scaled timeout."""
    adapter = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    assert adapter._rpc_client().timeout == 30
    set_factor(3.0)
    try:
        assert adapter._rpc_client().timeout == 90
    finally:
        set_factor(1.0)


def test_log_path_is_the_regtest_debug_log(tmp_path: Path) -> None:
    """`debug.log` under the chain's directory, read into `start`'s errors."""
    adapter = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    assert adapter.log_path == tmp_path / "regtest" / "debug.log"
    assert adapter._log_path() == adapter.log_path


def test_stop_sends_sigint(tmp_path: Path) -> None:
    """`stop` asks florestad to shut down with SIGINT, not SIGTERM."""
    adapter = FlorestadAdapter("florestad", tmp_path, 18443, 18444)
    process = MagicMock()
    adapter._signal_stop(process)
    process.send_signal.assert_called_once_with(signal.SIGINT)
    process.terminate.assert_not_called()
