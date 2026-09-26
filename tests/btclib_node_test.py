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
    """Only `CONNECT` is class-wide; the probed ones are per instance."""
    assert BtclibNodeAdapter.capabilities == frozenset({Capability.CONNECT})


def test_capabilities_gain_rpc_auth_config_where_the_build_writes_a_cookie(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1070 executable declares both."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.RPC_AUTH_CONFIG}
    )


def test_capabilities_gain_rpc_auth_negation_where_the_build_negates(
    tmp_path: Path,
) -> None:
    """An instance built with a `-norpcauth`-reading executable declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=True),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.RPC_AUTH_CONFIG, Capability.RPC_AUTH_NEGATION}
    )


def test_capabilities_gain_inbound_eviction_where_the_build_evicts(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1064 executable declares eviction."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=True),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.INBOUND_EVICTION}
    )


def test_capabilities_gain_mine_where_the_build_connects_alone(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1152 executable declares mining."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=True),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset({Capability.CONNECT, Capability.MINE})


def test_capabilities_stay_connect_alone_where_the_build_does_not(
    tmp_path: Path,
) -> None:
    """An instance built with a pre-1070 executable keeps the class set."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
    ):
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


def test_log_path_is_the_datadir_s_own_regtest_history_log(tmp_path: Path) -> None:
    """The disk family's own fact: `btclib_node`'s own log, unwritten yet."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.log_path == tmp_path / "regtest" / "history.log"


def test_log_path_read_on_a_start_timeout_is_log_path(tmp_path: Path) -> None:
    """What a `start` that times out reads back is `btclib_node`'s own log."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter._log_path() == adapter.log_path


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


def test_evicts_inbound_reads_the_probe_s_own_return_code() -> None:
    """`_evicts_inbound` is `import btclib_node.p2p.eviction` exiting zero."""
    btclib_node_module._evicts_inbound.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._evicts_inbound("fake-python-1064") is True
    run.assert_called_once_with(
        ["fake-python-1064", "-c", "import btclib_node.p2p.eviction"],
        check=False,
        capture_output=True,
    )


def test_evicts_inbound_is_false_when_the_import_fails() -> None:
    """A nonzero exit -- the module missing -- answers `False`."""
    btclib_node_module._evicts_inbound.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._evicts_inbound("fake-python-pre-1064") is False


def test_negates_rpcauth_reads_the_probe_s_own_return_code() -> None:
    """`_negates_rpcauth` is `_NEGATION_PROBE` exiting zero."""
    btclib_node_module._negates_rpcauth.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._negates_rpcauth("fake-python-1165") is True
    run.assert_called_once_with(
        ["fake-python-1165", "-c", btclib_node_module._NEGATION_PROBE],
        check=False,
        capture_output=True,
    )


def test_negates_rpcauth_is_false_when_the_parse_refuses() -> None:
    """A nonzero exit -- `-norpcauth` refused, or `tf2` kept -- is `False`."""
    btclib_node_module._negates_rpcauth.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=2)):
        assert btclib_node_module._negates_rpcauth("fake-python-pre-1165") is False


def test_connects_alone_reads_the_probe_s_own_return_code() -> None:
    """`_connects_alone` is `_SOLO_CONNECT_PROBE` exiting zero."""
    btclib_node_module._connects_alone.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._connects_alone("fake-python-1152") is True
    run.assert_called_once_with(
        ["fake-python-1152", "-c", btclib_node_module._SOLO_CONNECT_PROBE],
        check=False,
        capture_output=True,
    )


def test_connects_alone_is_false_where_the_status_gates() -> None:
    """A nonzero exit -- `update_chain` returned, or raised -- is `False`."""
    btclib_node_module._connects_alone.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._connects_alone("fake-python-1071") is False


class _FakeMiniWallet:
    """`MiniWallet`'s own `generate`, answering fixed header hashes."""

    hashes = (b"\x01" * 32, b"\x02" * 32)

    def __init__(self, node: object) -> None:
        self.node = node

    def generate(self, count: int) -> list[bytes]:
        return list(self.hashes[:count])


class _FakeTipRpc:
    """`getbestblockhash` answering each of `tips` in turn, then the last."""

    def __init__(self, *tips: str) -> None:
        self.tips = list(tips)
        self.calls = 0

    def call(self, method: str, params: list[object] | None = None) -> str:
        assert method == "getbestblockhash"
        assert params is None
        self.calls += 1
        return self.tips.pop(0) if len(self.tips) > 1 else self.tips[0]


def test_mine_returns_the_hashes_once_the_last_is_the_tip(tmp_path: Path) -> None:
    """`mine` polls `getbestblockhash` past a stale tip, then returns hex."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    rpc = _FakeTipRpc("01" * 32, "02" * 32)
    with (
        patch.object(btclib_node_module, "MiniWallet", _FakeMiniWallet),
        patch.object(adapter, "_rpc_client", return_value=rpc),
    ):
        hashes = adapter.mine(2)
    assert hashes == ["01" * 32, "02" * 32]
    assert rpc.calls == 2


def test_mine_zero_blocks_asks_the_node_nothing(tmp_path: Path) -> None:
    """`mine(0)` answers `[]` and polls no tip."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    rpc = _FakeTipRpc("00" * 32)
    with (
        patch.object(btclib_node_module, "MiniWallet", _FakeMiniWallet),
        patch.object(adapter, "_rpc_client", return_value=rpc),
    ):
        assert adapter.mine(0) == []
    assert rpc.calls == 0
