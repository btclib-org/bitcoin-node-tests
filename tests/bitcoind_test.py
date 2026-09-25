# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`'s own command line, RPC client and `mine`."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

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
        }
    )


def test_command_is_a_loopback_only_ephemeral_regtest(tmp_path: Path) -> None:
    """The argv names regtest, the datadir, both ports, loopback only."""
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
    adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    client = adapter._rpc_client()
    assert client.cookie_path == tmp_path / "regtest" / ".cookie"
    assert client.url == "http://127.0.0.1:18443"


def test_debug_log_path_is_the_datadir_s_own_regtest_debug_log(
    tmp_path: Path,
) -> None:
    """`Capability.DEBUG_LOG`'s own fact: bitcoind's own log, unwritten yet."""
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
    """`-bind`, this adapter's own p2p option, is refused rather than reused."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -bind\b"):
        BitcoindAdapter(
            "bitcoind", tmp_path, 18443, 18444, extra_args=["-bind=127.0.0.1:1"]
        )


def test_init_accepts_extra_args_naming_no_option_of_the_command(
    tmp_path: Path,
) -> None:
    """`-uacomment`, an option this adapter never sets, still passes through."""
    adapter = BitcoindAdapter(
        "bitcoind", tmp_path, 18443, 18444, extra_args=["-uacomment=foo"]
    )
    assert adapter._extra_args == ("-uacomment=foo",)


def test_mine_refuses_an_answer_that_is_not_a_list(tmp_path: Path) -> None:
    """A `generatetoaddress` answering anything but a list is refused."""
    adapter = BitcoindAdapter("bitcoind", tmp_path, 18443, 18444)
    rpc = _FakeRpc()
    rpc._answers["generatetoaddress"] = None

    with (
        patch.object(adapter, "_rpc_client", return_value=rpc),
        pytest.raises(TypeError, match="not a list"),
    ):
        adapter.mine()
