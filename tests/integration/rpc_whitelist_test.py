# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_whitelist`, one body over each node.

Read from Core's `test/functional/rpc_whitelist.py` (`fa24693819e0`,
2026-05-26), disk-family mechanism alone (issue btclib-org/btclib#2220,
[ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)):
`rpcauth`, `rpcwhitelist` and `rpcwhitelistdefault` are `bitcoin.conf`
keys, written to the datadir this adapter is given before it ever
starts -- no `extra_args` and no adapter change, `bitcoin.conf` living
at the same path a caller already holds (`datadir_path`'s own
constructor argument).

A smaller claim than Core's own file, declared rather than silent: two
users rather than Core's `strange_users` roster of malformed-input
edge cases, which asks what a hand-written parser does with a blank or
a doubled permission list rather than what `rpcwhitelist` restricts --
a claim about this project's own config parser, not about the
mechanism `Capability.RPC_AUTH_CONFIG` names. The `rpcauth` credential
below is generated the way Core's own `share/rpcauth/rpcauth.py`
generates one (`salt$hmac_sha256(salt, password)`), read from that
script rather than run: this repository ships no copy of it.

`Capability.RPC_AUTH_CONFIG` is asked before `bitcoin.conf` is written,
so a build without it skips before the data directory exists.
`btclib_node.py`'s own docstring is where that capability's
per-executable probe is argued.

Each `rpc_whitelist_<node>_test.py` module beside this one runs it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import base64
import hmac
import http.client
import json
import secrets
from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "rpcwhitelist_restricts_a_users_own_rpc_surface",
    "rpcwhitelistdefault_governs_an_unlisted_user",
]


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


def rpcwhitelist_restricts_a_users_own_rpc_surface(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a whitelisted user reaches only its own methods; others answer 403.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    datadir.mkdir()
    (datadir / "bitcoin.conf").write_text(
        "rpcwhitelistdefault=0\n"
        f"rpcauth={_rpcauth_line('alice', 'alicepw')}\n"
        "rpcwhitelist=alice:getbestblockhash,getblockcount\n"
        f"rpcauth={_rpcauth_line('bob', 'bobpw')}\n"
        "rpcwhitelist=bob:getblockcount\n"
    )
    adapter.start()
    try:
        assert _call(rpc_port, "alice", "alicepw", "getbestblockhash") == 200
        assert _call(rpc_port, "alice", "alicepw", "getblockcount") == 200
        assert _call(rpc_port, "alice", "alicepw", "getblockchaininfo") == 403
        assert _call(rpc_port, "bob", "bobpw", "getblockcount") == 200
        assert _call(rpc_port, "bob", "bobpw", "getbestblockhash") == 403
        assert _call(rpc_port, "alice", "wrong", "getblockcount") == 401
    finally:
        adapter.stop()


def rpcwhitelistdefault_governs_an_unlisted_user(
    make_adapter: AdapterFactory,
    cls: type[NodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `rpcwhitelistdefault=1` refuses a user `rpcwhitelist` never named.

    :param make_adapter: the session's own adapter factory.
    :param cls: a node's own adapter class.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    require(Capability.RPC_AUTH_CONFIG, adapter.capabilities, skip_counts)
    datadir.mkdir()
    (datadir / "bitcoin.conf").write_text(
        "rpcwhitelistdefault=1\n"
        f"rpcauth={_rpcauth_line('carol', 'carolpw')}\n"
        # `NodeAdapter.start` polls `getblockchaininfo` over the cookie this
        # adapter authenticates with (`node.py`'s own `_wait_for_rpc`), and
        # `rpcwhitelistdefault=1` restricts `__cookie__` exactly as it
        # restricts any other user -- Core's own test whitelists it too,
        # for the same reason, once it turns this setting on.
        "rpcwhitelist=__cookie__:getblockchaininfo\n"
    )
    adapter.start()
    try:
        assert _call(rpc_port, "carol", "carolpw", "getbestblockhash") == 403
    finally:
        adapter.stop()
