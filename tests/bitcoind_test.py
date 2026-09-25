# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`'s own command line, RPC client, `mine`, `_has_wallet`."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from bitcoin_node_tests import bitcoind as bitcoind_module
from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability


def test_capabilities_are_every_one_this_repository_names() -> None:
    """Bitcoind offers every one this repository names, `CLOCK` included."""
    assert BitcoindAdapter.capabilities == frozenset(
        {
            Capability.MINE,
            Capability.CONNECT,
            Capability.RAW_MESSAGE,
            Capability.BLK_FILES,
            Capability.DEBUG_LOG,
            Capability.UA_COMMENT,
            Capability.CLOCK,
            Capability.RPC_AUTH_CONFIG,
            Capability.RPC_AUTH_NEGATION,
            Capability.TEST_ACTIVATION_HEIGHT,
        }
    )


def test_capabilities_stay_the_full_class_set_where_the_build_has_a_wallet(
    tmp_path: Path,
) -> None:
    """An instance built against a wallet-carrying binary keeps the class's."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    assert adapter.capabilities is BitcoindAdapter.capabilities


def test_capabilities_drop_mine_where_the_build_has_no_wallet(tmp_path: Path) -> None:
    """An instance built against a walletless binary loses `MINE` alone."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=False):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    assert adapter.capabilities == BitcoindAdapter.capabilities - {Capability.MINE}


def test_has_wallet_reads_the_probe_s_own_stdout() -> None:
    """`_has_wallet` is `-help` naming a "Wallet options:" group."""
    bitcoind_module._has_wallet.cache_clear()
    stdout = b"...\nWallet options:\n\n  -disablewallet\n..."
    with patch("subprocess.run", return_value=SimpleNamespace(stdout=stdout)) as run:
        assert bitcoind_module._has_wallet("fake-bitcoind-with-wallet") is True
    run.assert_called_once_with(
        ["fake-bitcoind-with-wallet", "-help", "-nosettings"],
        check=False,
        capture_output=True,
    )


def test_has_wallet_is_false_where_help_names_no_wallet_group() -> None:
    """A build without wallet support never prints the group at all."""
    bitcoind_module._has_wallet.cache_clear()
    stdout = b"...\nZeroMQ notification options:\n..."
    with patch("subprocess.run", return_value=SimpleNamespace(stdout=stdout)):
        assert bitcoind_module._has_wallet("fake-bitcoind-without-wallet") is False


def test_has_wallet_is_cached_per_executable() -> None:
    """A second call for the same executable does not probe again."""
    bitcoind_module._has_wallet.cache_clear()
    stdout = b"...\nWallet options:\n"
    with patch("subprocess.run", return_value=SimpleNamespace(stdout=stdout)) as run:
        first = bitcoind_module._has_wallet("fake-bitcoind-cached")
        second = bitcoind_module._has_wallet("fake-bitcoind-cached")
    assert first is second is True
    run.assert_called_once()


def test_command_is_a_loopback_only_ephemeral_regtest(tmp_path: Path) -> None:
    """The argv names regtest, the datadir, both ports, loopback only."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    command = adapter._command()
    assert command[0] == "bitcoind"
    assert "-regtest" in command
    assert f"-datadir={tmp_path}" in command
    assert "-rpcport=18443" in command
    assert "-rpcbind=127.0.0.1" in command
    assert "-bind=127.0.0.1:18444" in command
    assert "-printtoconsole=0" in command
    assert "-debug=net" in command


def test_rpc_client_authenticates_by_the_datadir_s_cookie(tmp_path: Path) -> None:
    """The RPC client reads `<datadir>/regtest/.cookie`, unread so far."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    client = adapter._rpc_client()
    assert client.cookie_path == tmp_path / "regtest" / ".cookie"
    assert client.url == "http://127.0.0.1:18443"


def test_rpc_client_authenticates_with_rpc_auth_where_given(tmp_path: Path) -> None:
    """`rpc_auth` overrides the cookie: no file is ever read for it."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter(
            "bitcoind", tmp_path, 18443, 18444, rpc_auth=("bob", "bobpw")
        )
    client = adapter._rpc_client()
    assert client.cookie_path is None
    assert client.user == "bob"
    assert client.url == "http://127.0.0.1:18443"


def test_debug_log_path_is_the_datadir_s_own_regtest_debug_log(
    tmp_path: Path,
) -> None:
    """`Capability.DEBUG_LOG`'s own fact: bitcoind's own log, unwritten yet."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    assert adapter.debug_log_path == tmp_path / "regtest" / "debug.log"


class _FakeRpc:
    """Enough of `BitcoinCoreRpcClient` for `mine`: `call`, and `for_wallet`."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Any] | None]] = []
        self._answers: dict[str, Any] = {
            "getnewaddress": "bcrt1qexampleaddress",
            "generatetoaddress": ["a" * 64],
        }

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        self.calls.append((method, params))
        return self._answers.get(method)

    def for_wallet(self, name: str) -> _FakeRpc:
        self.calls.append(("for_wallet", [name]))
        return self


def test_mine_creates_a_wallet_once_and_generates_to_it(tmp_path: Path) -> None:
    """`mine` creates the wallet once, then mines to a fresh address."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    rpc = _FakeRpc()

    with patch.object(adapter, "_rpc_client", return_value=rpc):
        first = adapter.mine(1)
        second = adapter.mine(2)

    assert first == second == ["a" * 64]
    assert rpc.calls.count(("createwallet", ["miner"])) == 1
    assert ("generatetoaddress", [1, "bcrt1qexampleaddress"]) in rpc.calls
    assert ("generatetoaddress", [2, "bcrt1qexampleaddress"]) in rpc.calls


def test_init_refuses_extra_args_naming_bind_the_command_sets(tmp_path: Path) -> None:
    """`-bind`, this adapter's own p2p option, is refused rather than reused.

    Raised by `NodeAdapter.__init__` (`node.py`) before `_has_wallet` is
    ever probed, so this needs no patch of it.
    """
    with pytest.raises(ValueError, match=r"^extra_args reuses -bind\b"):
        BitcoindAdapter(
            "bitcoind", tmp_path, 18443, 18444, extra_args=["-bind=127.0.0.1:1"]
        )


def test_init_accepts_extra_args_naming_no_option_of_the_command(
    tmp_path: Path,
) -> None:
    """`-uacomment`, an option this adapter never sets, still passes through."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter(
            "bitcoind", tmp_path, 18443, 18444, extra_args=["-uacomment=foo"]
        )
    assert adapter._extra_args == ("-uacomment=foo",)


def test_mine_refuses_an_answer_that_is_not_a_list(tmp_path: Path) -> None:
    """A `generatetoaddress` answering anything but a list is refused."""
    with patch.object(bitcoind_module, "_has_wallet", return_value=True):
        adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    rpc = _FakeRpc()
    rpc._answers["generatetoaddress"] = None

    with (
        patch.object(adapter, "_rpc_client", return_value=rpc),
        pytest.raises(TypeError, match="not a list"),
    ):
        adapter.mine()
