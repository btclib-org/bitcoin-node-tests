# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_users`, rewritten on this harness: btclib-node.

The same claim `rpc_users_bitcoind_test.py` makes, against the target
rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
`Capability.RPC_AUTH_CONFIG` is checked against a constructed instance's
own `capabilities`, never the class's, exactly as
`rpc_whitelist_btclib_node_test.py` already does. `-rpcauth` and
`-rpccookieperms` are neither of them recognised at all -- not in
`bitcoin.conf`, not on the command line -- by a build before
[ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070),
so every test here counts a skip against that build rather than running
against it partway.

A malformed `-rpcauth` value refuses with `Error: Invalid -rpcauth
argument.` on a build past that issue -- `rpc/auth.py`'s own
`RpcAuthEntry.parse`, raised from `cli.py`'s own `build_config` and
caught there, never bitcoind's generic wording
(`rpc_users_bitcoind_test.py`'s own `_INIT_ERROR`); measured live at
`btclib-node` `cd61579e634787829206dc336c94affa0b58f5cf`. A cookie the
node cannot write is a different failure, inside `Node.run` rather than
`build_config`, and it answers with bitcoind's own wording after all:
`__init__.py`'s own `RPC_INIT_ERROR` constant is that string verbatim,
raised whenever `rpc_manager.start_listener()` fails for any reason,
cookie generation included -- measured live, a directory sitting where
the cookie file must go refuses with `Error: Unable to start HTTP
server. See debug log for details.`, the identical wording bitcoind's
own test names for the same scenario.

Ported, against its own capability: Core's own "interactions between
blank and non-blank rpcauth" check, below -- `config.py`'s own
`tuple(RpcAuthEntry.parse(value) for value in rpcauth)` raises on the
first value that fails to parse regardless of where it sits among the
well-formed ones, so a blank `-rpcauth=` refuses startup wherever it is
given among named entries, measured live in every ordering Core's own
file checks. Ported too, but never run here: Core's own "-norpcauth
disables previous -rpcauth params" check, gated on
`Capability.RPC_AUTH_NEGATION` (`capability.py`) rather than folded into
`RPC_AUTH_CONFIG` -- `-norpcauth` is not one of `cli.py`'s own
registered flags on either build measured, released or the `main` sha
named above, refused before a node ever starts (`Error parsing command
line arguments: Invalid parameter -norpcauth` on `main`, argparse's own
"unrecognized arguments" on the released build) rather than accepted and
disabling anything the way Core's own negation does
([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)).
`BtclibNodeAdapter` never declares the capability, on either build, so
this test's own row here is a counted skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_users_btclib_node_test.py
"""

from __future__ import annotations

import base64
import hmac
import http.client
import json
import secrets
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# The same malformed values `rpc_users_bitcoind_test.py` names, whose
# own module docstring has the reason a bare `-rpcauth` is not among
# them.
_MALFORMED_RPCAUTH = (
    "-rpcauth=",
    '-rpcauth=""',
    "-rpcauth=foo",
    "-rpcauth=foo:bar",
    "-rpcauth=foo:bar:baz",
    "-rpcauth=foo$bar:baz",
    "-rpcauth=foo$bar$baz",
)

# `rpc/auth.py`'s own `RpcAuthEntry.parse`, raised through `cli.py`'s
# own `build_config` and printed by `main`'s own `except ValueError`.
_MALFORMED_ERROR = "Invalid -rpcauth argument"

# `__init__.py`'s own `RPC_INIT_ERROR`, bitcoind's wording verbatim --
# this module's own docstring has the measurement.
_INIT_ERROR = "Unable to start HTTP server"

# The same named, well-formed `-rpcauth` entries
# `rpc_users_bitcoind_test.py` uses for the same check.
_RPCAUTH_USER1 = (
    "-rpcauth=user1:6dd184e5e69271fdd69103464630014f"
    "$eb3d7ce67c4d1ff3564270519b03b636c0291012692a5fa3dd1d2075daedd07b"
)
_RPCAUTH_USER2 = (
    "-rpcauth=user2:57b2f77c919eece63cfa46c2f06e46ae"
    "$266b63902f99f97eeaab882d4a87f8667ab84435c3799f2ce042ef5a994d620b"
)


def _rpcauth_line(username: str, password: str) -> str:
    """Return `username:salt$hash`, Core's own `rpcauth.py` own hash.

    :param username: the RPC user this line authenticates.
    :param password: that user's own plaintext password.
    """
    salt = secrets.token_hex(16)
    digest = hmac.new(salt.encode(), password.encode(), "sha256").hexdigest()
    return f"{username}:{salt}${digest}"


def _call(port: int, user: str, password: str, method: str) -> int:
    """Return the HTTP status `method` answers with, under basic auth.

    :param port: the node's own RPC port.
    :param user: the RPC username to authenticate as.
    :param password: that user's own plaintext password.
    :param method: the RPC method named, with no parameters.
    """
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    conn = http.client.HTTPConnection("127.0.0.1", port)
    try:
        conn.request("POST", "/", json.dumps({"method": method}), headers)
        return conn.getresponse().status
    finally:
        conn.close()


def test_rpcauth_via_config_authenticates_and_refuses(
    btclib_node_python: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A correct `rpcauth` credential from `bitcoin.conf` passes; others 401."""
    datadir = tmp_path / "datadir"
    rpc_port = free_port()
    adapter = BtclibNodeAdapter(btclib_node_python, datadir, rpc_port, free_port())
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    datadir.mkdir()
    (datadir / "bitcoin.conf").write_text(
        f"rpcauth={_rpcauth_line('alice', 'alicepw')}\n"
    )
    adapter.start()
    try:
        assert _call(rpc_port, "alice", "alicepw", "getbestblockhash") == 200
        assert _call(rpc_port, "alice", "wrongpw", "getbestblockhash") == 401
        assert _call(rpc_port, "eve", "alicepw", "getbestblockhash") == 401
        assert _call(rpc_port, "eve", "wrongpw", "getbestblockhash") == 401
    finally:
        adapter.stop()


def test_rpcauth_on_command_line_authenticates(
    btclib_node_python: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """The same credential, given as `extra_args` instead, authenticates too."""
    datadir = tmp_path / "datadir"
    rpc_port = free_port()
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        datadir,
        rpc_port,
        free_port(),
        extra_args=(f"-rpcauth={_rpcauth_line('alice', 'alicepw')}",),
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    adapter.start()
    try:
        assert _call(rpc_port, "alice", "alicepw", "getbestblockhash") == 200
        assert _call(rpc_port, "alice", "wrongpw", "getbestblockhash") == 401
    finally:
        adapter.stop()


@pytest.mark.parametrize("rpcauth", _MALFORMED_RPCAUTH)
def test_malformed_rpcauth_refuses_to_start(
    btclib_node_python: str, tmp_path: Path, skip_counts: SkipCounts, rpcauth: str
) -> None:
    """A malformed `-rpcauth` value is fatal at startup."""
    datadir = tmp_path / "datadir"
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        datadir,
        free_port(),
        free_port(),
        extra_args=(rpcauth,),
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    with pytest.raises(RuntimeError, match=_MALFORMED_ERROR):
        adapter.start()


@pytest.mark.parametrize(
    "extra_args",
    [
        (_RPCAUTH_USER1, _RPCAUTH_USER2, "-rpcauth="),
        (_RPCAUTH_USER1, "-rpcauth=", _RPCAUTH_USER2),
        ("-rpcauth=", _RPCAUTH_USER1, _RPCAUTH_USER2),
    ],
)
def test_blank_rpcauth_refuses_regardless_of_position(
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    extra_args: tuple[str, ...],
) -> None:
    """A blank `-rpcauth=` is fatal wherever it sits among named entries."""
    datadir = tmp_path / "datadir"
    adapter = BtclibNodeAdapter(
        btclib_node_python, datadir, free_port(), free_port(), extra_args=extra_args
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    with pytest.raises(RuntimeError, match=_MALFORMED_ERROR):
        adapter.start()


def test_norpcauth_disables_previous_rpcauth(
    btclib_node_python: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`-norpcauth` disables every `-rpcauth` value given before it.

    `BtclibNodeAdapter` never declares `Capability.RPC_AUTH_NEGATION`, on
    either build, so this always skips -- this module's own docstring
    has the measurement.
    """
    datadir = tmp_path / "datadir"
    rpc_port = free_port()
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        datadir,
        rpc_port,
        free_port(),
        extra_args=(_RPCAUTH_USER1, _RPCAUTH_USER2, "-norpcauth"),
    )
    require(Capability.RPC_AUTH_NEGATION, adapter.capabilities, skip_counts)
    adapter.start()
    try:
        assert _call(rpc_port, "user1", "bitcoin", "getbestblockhash") == 401
        assert _call(rpc_port, "user2", "bitcoin", "getbestblockhash") == 401
    finally:
        adapter.stop()


@pytest.mark.parametrize(
    "perm, expected_mode",
    [(None, 0o600), ("owner", 0o600), ("group", 0o640), ("all", 0o644)],
)
def test_rpccookieperms_sets_posix_permission_bits(
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    perm: str | None,
    expected_mode: int,
) -> None:
    """`-rpccookieperms` sets the cookie's own mode; unset defaults to owner."""
    datadir = tmp_path / "datadir"
    extra_args = (f"-rpccookieperms={perm}",) if perm else ()
    adapter = BtclibNodeAdapter(
        btclib_node_python, datadir, free_port(), free_port(), extra_args=extra_args
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    adapter.start()
    try:
        cookie_path = datadir / "regtest" / ".cookie"
        actual_mode = cookie_path.stat().st_mode & 0o777
        assert actual_mode == expected_mode
    finally:
        adapter.stop()


def test_cookie_write_failure_aborts_the_node(
    btclib_node_python: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A directory sitting at the cookie path is a fatal init error."""
    datadir = tmp_path / "datadir"
    adapter = BtclibNodeAdapter(btclib_node_python, datadir, free_port(), free_port())
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    cookie_dir = datadir / "regtest"
    cookie_dir.mkdir(parents=True)
    (cookie_dir / ".cookie.tmp").mkdir()
    with pytest.raises(RuntimeError, match=_INIT_ERROR):
        adapter.start()
