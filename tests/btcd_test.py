# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtcdAdapter`'s own command line and RPC client."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch
from urllib.request import Request

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter, _one_member, _v2_replies
from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter
from bitcoin_node_tests.timeout_factor import set_factor

if TYPE_CHECKING:
    from pathlib import Path


def test_capabilities_are_the_ones_btcd_answers() -> None:
    """The class declares what `btcd.py`'s own docstring measures."""
    assert BtcdAdapter.capabilities == frozenset(
        {
            Capability.MINE,
            Capability.CONNECT,
            Capability.INVALIDATE_BLOCK,
            Capability.CHAIN_TIPS,
            Capability.SIGN_MESSAGE_WITH_PRIVKEY,
        }
    )


def test_command_runs_btcd_on_regtest_over_loopback(tmp_path: Path) -> None:
    """Every option names the instance's own datadir, ports and credential."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444, rpc_auth=("bob", "pw"))
    assert adapter._command() == [
        "btcd",
        "--regtest",
        f"--datadir={tmp_path}",
        f"--logdir={tmp_path}",
        "--rpclisten=127.0.0.1:18443",
        "--notls",
        "--rpcuser=bob",
        "--rpcpass=pw",
        "--listen=127.0.0.1:18444",
    ]


def test_command_draws_a_password_per_instance(tmp_path: Path) -> None:
    """Without `rpc_auth`, each instance draws a password of its own."""
    first = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    second = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    assert "--rpcuser=tf2" in first._command()
    passwords = {
        arg
        for adapter in (first, second)
        for arg in adapter._command()
        if arg.startswith("--rpcpass=")
    }
    assert len(passwords) == 2


def test_init_refuses_extra_args_naming_an_option_of_the_command(
    tmp_path: Path,
) -> None:
    """`--rpcuser`, set by `_command`, is refused rather than reused."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -rpcuser\b"):
        BtcdAdapter("btcd", tmp_path, 18443, 18444, extra_args=["--rpcuser=x"])


@pytest.mark.parametrize("arg", ["-ufoo", "-u=foo", "-Pbar", "-b/tmp", "-Vu"])
def test_init_refuses_a_short_alias_of_an_option_of_the_command(
    tmp_path: Path, arg: str
) -> None:
    """`-u`, `-P` and `-b` are `--rpcuser`, `--rpcpass` and `--datadir`."""
    with pytest.raises(ValueError, match=r"^extra_args reuses -"):
        BtcdAdapter("btcd", tmp_path, 18443, 18444, extra_args=[arg])


@pytest.mark.parametrize("arg", ["-dinfo", "-Vd", "-V", "-x", "plain"])
def test_init_accepts_a_short_alias_of_no_option_of_the_command(
    tmp_path: Path, arg: str
) -> None:
    """`-d` is `--debuglevel`, which `_command` leaves unset."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444, extra_args=[arg])
    assert adapter._extra_args == (arg,)


def test_restart_refuses_a_short_alias_before_stopping(tmp_path: Path) -> None:
    """The refusal comes before `NodeAdapter.restart` is reached."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    with (
        patch.object(NodeAdapter, "restart") as restart,
        pytest.raises(ValueError, match=r"^extra_args reuses -rpcuser\b"),
    ):
        adapter.restart(["-ufoo"])
    restart.assert_not_called()


@pytest.mark.parametrize("extra_args", [None, ["-dinfo"]])
def test_restart_hands_accepted_args_to_the_base(
    tmp_path: Path, extra_args: list[str] | None
) -> None:
    """`None` and an accepted entry reach `NodeAdapter.restart` unchanged."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    with patch.object(NodeAdapter, "restart") as restart:
        adapter.restart(extra_args)
    restart.assert_called_once_with(extra_args)


def test_init_refuses_a_chain_other_than_regtest(tmp_path: Path) -> None:
    """Regtest is the one chain this adapter starts."""
    with pytest.raises(ValueError, match="cannot start a node on chain 'signet'"):
        BtcdAdapter("btcd", tmp_path, 18443, 18444, chain="signet")


def test_stdout_is_discarded() -> None:
    """Btcd prints its log to stdout as well as to `btcd.log`."""
    assert BtcdAdapter._discards_stdout


def test_rpc_client_authenticates_with_the_command_s_credential(
    tmp_path: Path,
) -> None:
    """The client's user and url are the ones `_command` starts btcd with."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444, rpc_auth=("bob", "pw"))
    client = adapter._rpc_client()
    assert client.user == "bob"
    assert client.url == "http://127.0.0.1:18443"


def test_rpc_client_timeout_is_scaled_by_the_global_factor(tmp_path: Path) -> None:
    """A call is bounded by the scaled timeout."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    assert adapter._rpc_client().timeout == 30
    set_factor(3.0)
    try:
        assert adapter._rpc_client().timeout == 90
    finally:
        set_factor(1.0)


def test_log_path_is_the_regtest_btcd_log(tmp_path: Path) -> None:
    """`btcd.log` under the chain's subdirectory, read into `start`'s errors."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    assert adapter.log_path == tmp_path / "regtest" / "btcd.log"
    assert adapter._log_path() == adapter.log_path


def test_dial_calls_addnode_onetry_with_two_arguments(tmp_path: Path) -> None:
    """Btcd's `addnode` takes no transport argument."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    with patch.object(BtcdAdapter, "_rpc_client") as client:
        adapter.dial("127.0.0.1:1", v2transport=False)
    client.return_value.call.assert_called_once_with(
        "addnode", ["127.0.0.1:1", "onetry"]
    )


def test_dial_refuses_v2transport(tmp_path: Path) -> None:
    """A BIP324 dial is refused before any call is made."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    with (
        patch.object(BtcdAdapter, "_rpc_client") as client,
        pytest.raises(ValueError, match="--v2transport"),
    ):
        adapter.dial("127.0.0.1:1", v2transport=True)
    client.assert_not_called()


@pytest.mark.parametrize(
    "reply, expected",
    [
        (
            {"jsonrpc": "2.0", "result": 0, "error": None, "id": "a"},
            {"jsonrpc": "2.0", "result": 0, "id": "a"},
        ),
        (
            {"jsonrpc": "2.0", "result": None, "error": {"code": -1}, "id": "a"},
            {"jsonrpc": "2.0", "error": {"code": -1}, "id": "a"},
        ),
        (
            {"jsonrpc": "2.0", "result": 0, "error": {"code": -1}, "id": "a"},
            {"jsonrpc": "2.0", "result": 0, "error": {"code": -1}, "id": "a"},
        ),
        (
            {"jsonrpc": "2.0", "result": 0, "id": "a"},
            {"jsonrpc": "2.0", "result": 0, "id": "a"},
        ),
        (
            {"result": 0, "error": None, "id": "a"},
            {"result": 0, "error": None, "id": "a"},
        ),
        ("not an object", "not an object"),
    ],
)
def test_one_member_drops_the_null_member_of_a_2_0_reply(
    reply: object, expected: object
) -> None:
    """Only a 2.0 reply carrying both members, one of them null, changes."""
    assert _one_member(reply) == expected


class _Answer:
    """An `HttpTransport` answering `body` with a 200."""

    def __init__(self, body: bytes) -> None:
        self.body = body

    def __call__(self, request: Request, timeout: float) -> tuple[int, bytes]:
        del request, timeout
        return 200, self.body


# a request no transport here reads
_REQUEST = Request("http://127.0.0.1:1")


def test_v2_replies_rewrites_a_single_reply_and_a_batch() -> None:
    """A reply object and each member of a batch lose their null member."""
    single = b'{"jsonrpc":"2.0","result":0,"error":null,"id":"a"}'
    status, body = _v2_replies(_Answer(single))(_REQUEST, 1.0)
    assert status == 200
    assert json.loads(body) == {"jsonrpc": "2.0", "result": 0, "id": "a"}
    batch = b'[{"jsonrpc":"2.0","result":0,"error":null,"id":"a"}]'
    _, body = _v2_replies(_Answer(batch))(_REQUEST, 1.0)
    assert json.loads(body) == [{"jsonrpc": "2.0", "result": 0, "id": "a"}]


def test_v2_replies_leaves_a_body_that_is_not_json() -> None:
    """An empty body, btcd's answer to a request without the marker, passes."""
    assert _v2_replies(_Answer(b"\n"))(_REQUEST, 1.0) == (200, b"\n")


def test_rpc_transport_translates_what_the_base_transport_answers(
    tmp_path: Path,
) -> None:
    """The adapter's transport is the base one, through `_v2_replies`."""
    adapter = BtcdAdapter("btcd", tmp_path, 18443, 18444)
    base = _Answer(b'{"jsonrpc":"2.0","result":0,"error":null,"id":"a"}')
    with patch.object(NodeAdapter, "_rpc_transport", return_value=base):
        _, body = adapter._rpc_transport()(_REQUEST, 1.0)
    assert json.loads(body) == {"jsonrpc": "2.0", "result": 0, "id": "a"}
