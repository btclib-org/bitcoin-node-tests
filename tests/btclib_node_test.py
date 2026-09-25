# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`'s own command line and RPC client."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability


def test_capabilities_are_connect_alone() -> None:
    """`Capability.MINE` is not declared: ISS btclib-node#1071 is why."""
    assert BtclibNodeAdapter.capabilities == frozenset({Capability.CONNECT})


def test_command_runs_python_dash_m_btclib_node(tmp_path: Path) -> None:
    """The argv is `python -m btclib_node ...`, never the console script."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    command = adapter._command()
    assert command[:3] == [sys.executable, "-m", "btclib_node"]
    assert "-regtest" in command
    assert f"-datadir={tmp_path}" in command
    assert "-rpcport=18443" in command
    assert "-rpcbind=127.0.0.1" in command
    assert "-port=18444" in command


def test_rpc_client_authenticates_with_a_placeholder_credential(tmp_path: Path) -> None:
    """The RPC client carries a credential the node ignores, no cookie."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    client = adapter._rpc_client()
    assert client.cookie_path is None
    assert client.user == "tf2"
    assert client.url == "http://127.0.0.1:18443"


def test_init_refuses_extra_args_naming_port_the_command_sets(tmp_path: Path) -> None:
    """`-port`, this adapter's own p2p option, is refused rather than reused."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -port\b"):
        BtclibNodeAdapter(
            sys.executable, tmp_path, 18443, 18444, extra_args=["-port=1"]
        )


def test_init_accepts_extra_args_naming_no_option_of_the_command(
    tmp_path: Path,
) -> None:
    """`-uacomment`, an option this adapter never sets, still passes through."""
    adapter = BtclibNodeAdapter(
        sys.executable, tmp_path, 18443, 18444, extra_args=["-uacomment=foo"]
    )
    assert adapter._extra_args == ("-uacomment=foo",)
