# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_users`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/rpc_users.py` (`faf993ee4421`,
2026-05-26), disk-family mechanism alone (issue btclib-org/btclib#2220,
[ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)):
`rpcauth`, `rpcuser`/`rpcpassword` and `rpccookieperms` are each written
to the datadir this adapter is given, either through `bitcoin.conf`
before it ever starts or on the command line as `extra_args` -- neither
needs an adapter change, `NodeAdapter.__init__`'s own
`_check_extra_args` raising nothing for any of the three, none of them
an option `_command()` (`bitcoind.py`) sets itself.

A smaller claim than Core's own file, declared rather than silent.
Dropped: the `rpcauth.py` script Core's own harness runs as a
subprocess to generate two of its four credentials, and the
`SystemRandom`-chosen username -- both a claim about that script rather
than about `Capability.RPC_AUTH_CONFIG`, which `_rpcauth_line` below
generates a credential for the same way `rpc_whitelist_bitcoind_test.py`
already does. `-rpcuser`/`-rpcpassword` and `-norpccookiefile` each
write no RPC cookie, measured live against the pinned `31.1` --
`rpcauth` given alongside either does not bring the cookie back -- so a
client that waits on the cookie `_rpc_client()` (`bitcoind.py`)
otherwise reads never sees one and `start` timed out rather than the
node ever answering RPC
([ISS bitcoin-node-tests#34](https://github.com/btclib-org/bitcoin-node-tests/issues/34)).
`rpc_auth`
(`NodeAdapter.__init__`, `node.py`) is what lets them back in: the
caller that puts either flag in `extra_args` already knows the
plaintext credential it chose there, exactly as Core's own harness
knows the plaintext of whatever it wrote into `bitcoin.conf`, and
passes it to the adapter instead of leaving the readiness wait on a
cookie the node never writes. Core's own equivalent test hits the
identical gap for `-norpccookiefile` alone and works around it with
`busy_wait_for_debug_log`, an alternate readiness wait keyed on the
debug log rather than RPC -- unneeded here, since `-norpccookiefile`
below is paired with an `-rpcauth` value whose plaintext this file
already holds, unlike Core's own `test_norpccookiefile`, which pairs it
with a `-rpcauth` value `get_auth_cookie`
(`test_framework/util.py`) has no way to recover the plaintext of from
`bitcoin.conf` alone. Of Core's own `test_auth` combinations, the
`-rpcuser`/`-rpcpassword` test checks the right credential and a wrong
password only: the wrong user and the wrong pair go through the same
comparison (`CheckUserAuthorized`, `httprpc.cpp`) that
`test_rpcauth_via_config_authenticates_and_refuses` already drives
through all four. Ported, against its own capability rather than
`RPC_AUTH_CONFIG`: Core's own "-norpcauth disables previous -rpcauth
params" check, `Capability.RPC_AUTH_NEGATION`
(`capability.py`) -- a fact `BitcoindAdapter` declares unconditionally
and `BtclibNodeAdapter` never does, `cli.py` registering no `-no<name>`
negation for `-rpcauth` on either build measured
([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)),
so this test's own row on that node is a counted skip rather than a
narrowed run. Dropped last: `platform.system() == 'Windows'`
is never this repository's own gate (`CONTRIBUTING.md`'s own table: one
image, `ubuntu-latest`), so the branch `test_rpccookieperms` takes on
it is unreachable here and the POSIX permission check below is the
whole of that test.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import base64
import hmac
import http.client
import json
import secrets
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own malformed `-rpcauth` values, minus the bare `-rpcauth`
# flag with no value at all, dropped below: it exercises `argparse`'s
# own "expected one argument" on btclib-node rather than
# `Capability.RPC_AUTH_CONFIG`'s own credential parsing, which the
# other seven already cover between them. Every one of the rest
# refuses with the identical generic init error on bitcoind (measured
# live against the pinned `31.1`), unlike btclib-node's own build,
# which names the defect (`rpc_users_btclib_node_test.py`'s own module
# docstring). `-rpcauth=""` reaches each node's own argv as the two
# literal quote characters -- this harness passes `extra_args` straight
# to `subprocess.Popen`, with no shell in between to unquote them --
# rather than as an empty string; refused all the same, no `:` sitting
# in either character.
_MALFORMED_RPCAUTH = (
    "-rpcauth=",
    '-rpcauth=""',
    "-rpcauth=foo",
    "-rpcauth=foo:bar",
    "-rpcauth=foo:bar:baz",
    "-rpcauth=foo$bar:baz",
    "-rpcauth=foo$bar$baz",
)

# bitcoind's own `Error: Unable to start HTTP server. See debug log for
# details.`, the message every `assert_start_raises_init_error` call in
# Core's own file names for a malformed `-rpcauth` -- and the one a
# cookie-write failure raises too, `feature_filelock_bitcoind_test.py`'s
# own sibling shape for a resource this adapter's own datadir already
# holds.
_INIT_ERROR = "Unable to start HTTP server"

# Named, well-formed `-rpcauth` entries: pw is "bitcoin" for both,
# Core's own file's own credentials, kept for the same reason
# `_rpcauth_line`'s own values are made up instead -- only their shape
# matters here, not what they authenticate.
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
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A correct `rpcauth` credential from `bitcoin.conf` passes; others 401."""
    datadir = tmp_path / "datadir"
    datadir.mkdir()
    rpc_port, p2p_port = free_ports(2)
    (datadir / "bitcoin.conf").write_text(
        f"rpcauth={_rpcauth_line('alice', 'alicepw')}\n"
    )
    adapter = BitcoindAdapter(bitcoind_path, datadir, rpc_port, p2p_port)
    adapter.start()
    try:
        require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
        assert _call(rpc_port, "alice", "alicepw", "getbestblockhash") == 200
        assert _call(rpc_port, "alice", "wrongpw", "getbestblockhash") == 401
        assert _call(rpc_port, "eve", "alicepw", "getbestblockhash") == 401
        assert _call(rpc_port, "eve", "wrongpw", "getbestblockhash") == 401
    finally:
        adapter.stop()


def test_rpcauth_on_command_line_authenticates(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """The same credential, given as `extra_args` instead, authenticates too."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        datadir,
        rpc_port,
        p2p_port,
        extra_args=(f"-rpcauth={_rpcauth_line('alice', 'alicepw')}",),
    )
    adapter.start()
    try:
        require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
        assert _call(rpc_port, "alice", "alicepw", "getbestblockhash") == 200
        assert _call(rpc_port, "alice", "wrongpw", "getbestblockhash") == 401
    finally:
        adapter.stop()


@pytest.mark.parametrize("rpcauth", _MALFORMED_RPCAUTH)
def test_malformed_rpcauth_refuses_to_start(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts, rpcauth: str
) -> None:
    """A malformed `-rpcauth` value is fatal at startup."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path, datadir, rpc_port, p2p_port, extra_args=(rpcauth,)
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    with pytest.raises(RuntimeError, match=_INIT_ERROR):
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
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    extra_args: tuple[str, ...],
) -> None:
    """A blank `-rpcauth=` is fatal wherever it sits among named entries."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path, datadir, rpc_port, p2p_port, extra_args=extra_args
    )
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    with pytest.raises(RuntimeError, match=_INIT_ERROR):
        adapter.start()


def test_norpcauth_disables_previous_rpcauth(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`-norpcauth` disables every `-rpcauth` value given before it."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        datadir,
        rpc_port,
        p2p_port,
        extra_args=(_RPCAUTH_USER1, _RPCAUTH_USER2, "-norpcauth"),
    )
    adapter.start()
    try:
        require(Capability.RPC_AUTH_NEGATION, adapter.capabilities, skip_counts)
        assert _call(rpc_port, "user1", "bitcoin", "getbestblockhash") == 401
        assert _call(rpc_port, "user2", "bitcoin", "getbestblockhash") == 401
    finally:
        adapter.stop()


def test_rpcuser_rpcpassword_authenticates_without_a_cookie(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`-rpcuser`/`-rpcpassword` authenticates; no cookie is ever written."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        datadir,
        rpc_port,
        p2p_port,
        extra_args=("-rpcuser=bob", "-rpcpassword=bobpw"),
        rpc_auth=("bob", "bobpw"),
    )
    adapter.start()
    try:
        require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
        assert _call(rpc_port, "bob", "bobpw", "getbestblockhash") == 200
        assert _call(rpc_port, "bob", "wrongpw", "getbestblockhash") == 401
        assert not (datadir / "regtest" / ".cookie").exists()
    finally:
        adapter.stop()


def test_norpccookiefile_writes_no_cookie_and_rpcauth_still_authenticates(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`-norpccookiefile` writes no cookie; a paired `-rpcauth` still works."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        datadir,
        rpc_port,
        p2p_port,
        extra_args=(_RPCAUTH_USER1, "-norpccookiefile"),
        rpc_auth=("user1", "bitcoin"),
    )
    adapter.start()
    try:
        require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
        assert _call(rpc_port, "user1", "bitcoin", "getbestblockhash") == 200
        assert _call(rpc_port, "user1", "wrongpw", "getbestblockhash") == 401
        assert not (datadir / "regtest" / ".cookie").exists()
    finally:
        adapter.stop()


@pytest.mark.parametrize(
    "perm, expected_mode",
    [(None, 0o600), ("owner", 0o600), ("group", 0o640), ("all", 0o644)],
)
def test_rpccookieperms_sets_posix_permission_bits(
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    perm: str | None,
    expected_mode: int,
) -> None:
    """`-rpccookieperms` sets the cookie's own mode; unset defaults to owner."""
    datadir = tmp_path / "datadir"
    extra_args = (f"-rpccookieperms={perm}",) if perm else ()
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path, datadir, rpc_port, p2p_port, extra_args=extra_args
    )
    adapter.start()
    try:
        require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
        cookie_path = datadir / "regtest" / ".cookie"
        actual_mode = cookie_path.stat().st_mode & 0o777
        assert actual_mode == expected_mode
    finally:
        adapter.stop()


def test_cookie_write_failure_aborts_the_node(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A directory sitting at the cookie path is a fatal init error."""
    datadir = tmp_path / "datadir"
    cookie_dir = datadir / "regtest"
    cookie_dir.mkdir(parents=True)
    (cookie_dir / ".cookie.tmp").mkdir()
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(bitcoind_path, datadir, rpc_port, p2p_port)
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    with pytest.raises(RuntimeError, match=_INIT_ERROR):
        adapter.start()
