# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_whitelist`, rewritten on this harness: btclib-node.

The same claim `rpc_whitelist_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
`Capability.RPC_AUTH_CONFIG` is checked against a constructed instance's
own `capabilities`, never the class's -- `btclib_node.py`'s own
docstring is where that capability's own per-executable probe is
argued. Constructing an adapter spawns nothing, so the capability is
known before `bitcoin.conf` is even written: `TF2_BTCLIB_NODE_PYTHON`
naming a build with
[ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
runs the same assertions the oracle's own module does; one naming a
build without it -- PyPI's `2026.9.24` release, what this repository
pins today -- counts a skip instead of a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_whitelist_btclib_node_test.py
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
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


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


def test_rpcwhitelist_restricts_a_users_own_rpc_surface(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A whitelisted user reaches only its own methods; others answer 403."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, datadir, rpc_port, p2p_port
    )
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


def test_rpcwhitelistdefault_governs_an_unlisted_user(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """`rpcwhitelistdefault=1` refuses a user `rpcwhitelist` never named."""
    datadir = tmp_path / "datadir"
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BtclibNodeAdapter, btclib_node_python, datadir, rpc_port, p2p_port
    )
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
