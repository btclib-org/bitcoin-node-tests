# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`'s own command line and RPC client."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bitcoin_node_tests import btclib_node as btclib_node_module
from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability


def test_capabilities_are_connect_alone() -> None:
    """`Capability.MINE` is not declared: ISS btclib-node#1071 is why."""
    assert BtclibNodeAdapter.capabilities == frozenset({Capability.CONNECT})


def test_capabilities_gain_rpc_auth_config_where_the_build_writes_a_cookie(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1070 executable declares both."""
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.RPC_AUTH_CONFIG}
    )


def test_capabilities_stay_connect_alone_where_the_build_does_not(
    tmp_path: Path,
) -> None:
    """An instance built with a pre-1070 executable keeps the class set."""
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities is BtclibNodeAdapter.capabilities


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
    assert not any("-rpcuser" in arg or "-rpcpassword" in arg for arg in command)


def test_rpc_client_authenticates_with_a_placeholder_credential_pre_1070(
    tmp_path: Path,
) -> None:
    """A build with no `rpc.auth` module gets a credential it never checks."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False):
        client = adapter._rpc_client()
    assert client.cookie_path is None
    assert client.user == "tf2"
    assert client.url == "http://127.0.0.1:18443"


def test_rpc_client_authenticates_with_rpc_auth_where_given(tmp_path: Path) -> None:
    """`rpc_auth` overrides both the cookie and the placeholder credential."""
    adapter = BtclibNodeAdapter(
        sys.executable, tmp_path, 18443, 18444, rpc_auth=("bob", "bobpw")
    )
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True):
        client = adapter._rpc_client()
    assert client.cookie_path is None
    assert client.user == "bob"
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


def test_rpc_client_authenticates_by_the_datadir_s_cookie_post_1070(
    tmp_path: Path,
) -> None:
    """A build carrying `rpc.auth` gets `BitcoindAdapter`'s own cookie path."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True):
        client = adapter._rpc_client()
    assert client.cookie_path == tmp_path / "regtest" / ".cookie"
    assert client.url == "http://127.0.0.1:18443"


def test_writes_auth_cookie_reads_the_probe_s_own_return_code() -> None:
    """`_writes_auth_cookie` is `import btclib_node.rpc.auth` exiting zero."""
    btclib_node_module._writes_auth_cookie.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._writes_auth_cookie("fake-python-1070") is True
    run.assert_called_once_with(
        ["fake-python-1070", "-c", "import btclib_node.rpc.auth"],
        check=False,
        capture_output=True,
    )


def test_writes_auth_cookie_is_false_when_the_import_fails() -> None:
    """A nonzero exit -- the module missing -- answers `False`."""
    btclib_node_module._writes_auth_cookie.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._writes_auth_cookie("fake-python-pre-1070") is False


def test_writes_auth_cookie_is_cached_per_executable() -> None:
    """A second call for the same executable does not probe again."""
    btclib_node_module._writes_auth_cookie.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        first = btclib_node_module._writes_auth_cookie("fake-python-cached")
        second = btclib_node_module._writes_auth_cookie("fake-python-cached")
    assert first is second is True
    run.assert_called_once()
