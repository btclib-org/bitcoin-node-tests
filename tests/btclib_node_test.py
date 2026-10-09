# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`'s own command line and RPC client."""

from __future__ import annotations

import os
import sys
from functools import _lru_cache_wrapper
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from bitcoin_node_tests import btclib_node as btclib_node_module
from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.timeout_factor import set_factor


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
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
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
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
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
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
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
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset({Capability.CONNECT, Capability.MINE})


def test_capabilities_gain_ban_where_the_build_serves_a_ban_list(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1088 executable declares banning."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=True),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset({Capability.CONNECT, Capability.BAN})


def test_capabilities_gain_min_relay_tx_fee_where_the_build_sets_it(
    tmp_path: Path,
) -> None:
    """An instance built with a post-1332 executable declares the floor."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=True),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.MIN_RELAY_TX_FEE}
    )


def test_capabilities_gain_permit_bare_multisig_where_the_build_reads_it(
    tmp_path: Path,
) -> None:
    """An instance built with a `-permitbaremultisig` build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=True),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.PERMIT_BARE_MULTISIG}
    )


def test_capabilities_gain_chain_tips_where_the_build_serves_them(
    tmp_path: Path,
) -> None:
    """An instance built with a `getchaintips`-serving build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=True),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.CHAIN_TIPS}
    )


def test_capabilities_gain_disconnect_where_the_build_serves_it(
    tmp_path: Path,
) -> None:
    """An instance built with a `disconnectnode`-serving build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=True),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.DISCONNECT}
    )


def test_capabilities_gain_package_acceptance_where_the_build_serves_it(
    tmp_path: Path,
) -> None:
    """An instance built with a `submitpackage`-serving build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=True),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.PACKAGE_ACCEPTANCE}
    )


def test_capabilities_gain_orphanage_where_the_build_serves_it(
    tmp_path: Path,
) -> None:
    """An instance built with a `getorphantxs`-serving build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=True),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset({Capability.CONNECT, Capability.ORPHANAGE})


def test_capabilities_gain_cluster_replacement_where_the_build_counts_clusters(
    tmp_path: Path,
) -> None:
    """An instance built with a cluster-counting build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=True),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.CLUSTER_REPLACEMENT}
    )


def test_capabilities_gain_listen_address_where_the_build_reads_bind(
    tmp_path: Path,
) -> None:
    """An instance built with a `-bind`-reading build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=True),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.LISTEN_ADDRESS}
    )


def test_capabilities_gain_v2transport_where_the_build_speaks_bip324(
    tmp_path: Path,
) -> None:
    """An instance built with a `-v2transport` build declares it."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=True),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities == frozenset(
        {Capability.CONNECT, Capability.V2TRANSPORT}
    )


def test_capabilities_stay_connect_alone_where_the_build_does_not(
    tmp_path: Path,
) -> None:
    """An instance built with a pre-1070 executable keeps the class set."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=False),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.capabilities is BtclibNodeAdapter.capabilities


def test_command_runs_python_dash_m_btclib_node(tmp_path: Path) -> None:
    """The argv is `python -m btclib_node ...`, never the console script."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    command = adapter._command()
    assert command[:3] == [sys.executable, "-m", "btclib_node"]
    assert "-chain=regtest" in command
    assert not {"-connect=0", "-listen=1"} & set(command)
    assert f"-datadir={tmp_path}" in command
    assert "-rpcport=18443" in command
    assert "-rpcbind=127.0.0.1" in command
    assert "-port=18444" in command
    assert not any("-rpcuser" in arg or "-rpcpassword" in arg for arg in command)


def test_chains_are_every_one_the_node_names() -> None:
    """Core's own `-chain=` vocabulary, `testnet4` aside."""
    assert BtclibNodeAdapter.chains == frozenset({"main", "test", "signet", "regtest"})


def test_init_refuses_testnet4(tmp_path: Path) -> None:
    """The one chain of Core's vocabulary this node does not resolve."""
    with pytest.raises(ValueError, match=r"cannot start a node on chain 'testnet4'"):
        BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444, chain="testnet4")


@pytest.mark.parametrize("chain", ["main", "test", "signet"])
def test_command_keeps_any_other_chain_off_the_network(
    tmp_path: Path, chain: str
) -> None:
    """Any chain but regtest names itself, dials nobody, and still listens."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444, chain=chain)
    command = adapter._command()
    assert f"-chain={chain}" in command
    assert {"-connect=0", "-listen=1", "-port=18444"} <= set(command)


@pytest.mark.parametrize(
    "chain, subdir",
    [
        ("main", "mainnet"),
        ("test", "testnet"),
        ("signet", "signet"),
        ("regtest", "regtest"),
    ],
)
def test_cookie_and_log_are_the_chain_s_own(
    tmp_path: Path, chain: str, subdir: str
) -> None:
    """Every chain writes below the datadir, in a directory of its own name."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444, chain=chain)
    with patch.object(btclib_node_module, "_writes_auth_cookie", return_value=True):
        client = adapter._rpc_client()
    assert client.cookie_path == tmp_path / subdir / ".cookie"
    assert adapter.log_path == tmp_path / subdir / "history.log"


def test_capabilities_drop_mine_on_another_chain(tmp_path: Path) -> None:
    """A build that connects alone still gains no `MINE` off regtest."""
    with (
        patch.object(btclib_node_module, "_writes_auth_cookie", return_value=False),
        patch.object(btclib_node_module, "_negates_rpcauth", return_value=False),
        patch.object(btclib_node_module, "_evicts_inbound", return_value=False),
        patch.object(btclib_node_module, "_connects_alone", return_value=True),
        patch.object(btclib_node_module, "_serves_ban_list", return_value=False),
        patch.object(btclib_node_module, "_sets_min_relay_fee", return_value=False),
        patch.object(btclib_node_module, "_serves_chain_tips", return_value=False),
        patch.object(btclib_node_module, "_serves_disconnect", return_value=False),
        patch.object(btclib_node_module, "_serves_submitpackage", return_value=False),
        patch.object(btclib_node_module, "_serves_getorphantxs", return_value=False),
        patch.object(btclib_node_module, "_replaces_by_cluster", return_value=False),
        patch.object(btclib_node_module, "_binds_address", return_value=False),
        patch.object(btclib_node_module, "_speaks_v2", return_value=False),
        patch.object(btclib_node_module, "_permits_bare_multisig", return_value=False),
    ):
        adapter = BtclibNodeAdapter(
            sys.executable, tmp_path, 18443, 18444, chain="signet"
        )
    assert adapter.capabilities is BtclibNodeAdapter.capabilities


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


@pytest.mark.parametrize(
    "rpc_auth, writes_cookie",
    [(("bob", "bobpw"), True), (None, True), (None, False)],
)
def test_rpc_client_timeout_is_scaled_by_the_global_factor(
    tmp_path: Path, rpc_auth: tuple[str, str] | None, writes_cookie: bool
) -> None:
    """Every credential path bounds a call by the scaled timeout."""
    adapter = BtclibNodeAdapter(
        sys.executable, tmp_path, 18443, 18444, rpc_auth=rpc_auth
    )
    with patch.object(
        btclib_node_module, "_writes_auth_cookie", return_value=writes_cookie
    ):
        assert adapter._rpc_client().timeout == 30
        set_factor(3.0)
        try:
            assert adapter._rpc_client().timeout == 90
        finally:
            set_factor(1.0)


def test_log_path_is_the_datadir_s_own_regtest_history_log(tmp_path: Path) -> None:
    """The disk family's own fact: `btclib_node`'s own log, unwritten yet."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter.log_path == tmp_path / "regtest" / "history.log"


def test_log_path_read_on_a_start_timeout_is_log_path(tmp_path: Path) -> None:
    """What a `start` that times out reads back is `btclib_node`'s own log."""
    adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
    assert adapter._log_path() == adapter.log_path


def _assert_probed_in_own_home(run: Mock, executable: str, probe: str) -> None:
    """Assert `run` was called once, with `probe` and a `HOME` of its own."""
    run.assert_called_once()
    assert run.call_args.args == ([executable, "-c", probe],)
    env = run.call_args.kwargs["env"]
    assert env["HOME"] != os.environ.get("HOME")
    assert env["USERPROFILE"] == env["HOME"]


@pytest.mark.parametrize(
    "probe, field",
    [
        (btclib_node_module._accepts_v1transport, "v1transport=True"),
        (btclib_node_module._speaks_v2, "v2transport=False"),
    ],
)
def test_a_config_probe_runs_in_a_home_of_its_own(
    probe: _lru_cache_wrapper[bool],
    field: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The home `build_config` sees is a directory no other probe shares."""
    homes = tmp_path / "homes"
    package = tmp_path / "btclib_node"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text(
        "from pathlib import Path\n"
        "from types import SimpleNamespace\n"
        "def build_config(argv):\n"
        f"    with open({str(homes)!r}, 'a') as f:\n"
        "        f.write(str(Path.home()) + '\\n')\n"
        f"    return SimpleNamespace({field})\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    answers = []
    for _ in range(2):
        probe.cache_clear()
        answers.append(probe(sys.executable))
    probe.cache_clear()
    first, second = homes.read_text().splitlines()
    assert answers == [True, True]
    assert first != second
    assert Path.home() not in (Path(first), Path(second))
    assert not Path(first).exists()


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
    _assert_probed_in_own_home(
        run, "fake-python-1165", btclib_node_module._NEGATION_PROBE
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


def test_serves_ban_list_reads_the_probe_s_own_return_code() -> None:
    """`_serves_ban_list` is `_BAN_PROBE` exiting zero."""
    btclib_node_module._serves_ban_list.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._serves_ban_list("fake-python-1088") is True
    run.assert_called_once_with(
        ["fake-python-1088", "-c", btclib_node_module._BAN_PROBE],
        check=False,
        capture_output=True,
    )


def test_serves_ban_list_is_false_where_the_table_lacks_them() -> None:
    """A nonzero exit -- a ban RPC missing, or no such table -- is `False`."""
    btclib_node_module._serves_ban_list.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._serves_ban_list("fake-python-pre-1088") is False


def test_serves_chain_tips_reads_the_probe_s_own_return_code() -> None:
    """`_serves_chain_tips` is `_CHAIN_TIPS_PROBE` exiting zero."""
    btclib_node_module._serves_chain_tips.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._serves_chain_tips("fake-python-main") is True
    run.assert_called_once_with(
        ["fake-python-main", "-c", btclib_node_module._CHAIN_TIPS_PROBE],
        check=False,
        capture_output=True,
    )


def test_serves_chain_tips_is_false_where_the_table_lacks_it() -> None:
    """A nonzero exit -- the RPC missing, or no such table -- is `False`."""
    btclib_node_module._serves_chain_tips.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._serves_chain_tips("fake-python-release") is False


def test_serves_disconnect_reads_the_probe_s_own_return_code() -> None:
    """`_serves_disconnect` is `_DISCONNECT_PROBE` exiting zero."""
    btclib_node_module._serves_disconnect.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._serves_disconnect("fake-python-main") is True
    run.assert_called_once_with(
        ["fake-python-main", "-c", btclib_node_module._DISCONNECT_PROBE],
        check=False,
        capture_output=True,
    )


def test_serves_disconnect_is_false_where_the_table_lacks_it() -> None:
    """A nonzero exit -- the RPC missing, or no such table -- is `False`."""
    btclib_node_module._serves_disconnect.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._serves_disconnect("fake-python-release") is False


@pytest.mark.parametrize(
    "callbacks, served",
    [
        ('{"disconnectnode": None}', True),
        ('{"getblockcount": None}', False),
        ('{"getblockcount": "disconnectnode"}', False),
        ("[]", False),
    ],
)
def test_disconnect_probe_answers_from_the_table_s_keys(
    callbacks: str, served: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_DISCONNECT_PROBE` answers from the keys of a stub `callbacks`."""
    package = tmp_path / "btclib_node" / "rpc"
    package.mkdir(parents=True)
    (tmp_path / "btclib_node" / "__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "callbacks.py").write_text(f"callbacks = {callbacks}\n")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._serves_disconnect.cache_clear()
    answer = btclib_node_module._serves_disconnect(sys.executable)
    btclib_node_module._serves_disconnect.cache_clear()
    assert answer is served


def test_replaces_by_cluster_reads_the_probe_s_own_return_code() -> None:
    """`_replaces_by_cluster` is `_CLUSTER_REPLACEMENT_PROBE` exiting zero."""
    btclib_node_module._replaces_by_cluster.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._replaces_by_cluster("fake-python-main") is True
    run.assert_called_once_with(
        ["fake-python-main", "-c", btclib_node_module._CLUSTER_REPLACEMENT_PROBE],
        check=False,
        capture_output=True,
    )


def test_replaces_by_cluster_is_false_where_the_check_is_missing() -> None:
    """A nonzero exit -- the method missing, or no such class -- is `False`."""
    btclib_node_module._replaces_by_cluster.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._replaces_by_cluster("fake-python-release") is False


@pytest.mark.parametrize(
    "body, counted",
    [
        ("def check_package_replacement(self): ...", True),
        ("def check_replacement(self): ...", False),
    ],
)
def test_cluster_replacement_probe_answers_from_the_class_s_methods(
    body: str, counted: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_CLUSTER_REPLACEMENT_PROBE` answers from a stub `Mempool`'s methods."""
    package = tmp_path / "btclib_node"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "mempool.py").write_text(f"class Mempool:\n    {body}\n")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._replaces_by_cluster.cache_clear()
    answer = btclib_node_module._replaces_by_cluster(sys.executable)
    btclib_node_module._replaces_by_cluster.cache_clear()
    assert answer is counted


def test_serves_submitpackage_reads_the_probe_s_own_return_code() -> None:
    """`_serves_submitpackage` is `_SUBMITPACKAGE_PROBE` exiting zero."""
    btclib_node_module._serves_submitpackage.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._serves_submitpackage("fake-python-main") is True
    run.assert_called_once_with(
        ["fake-python-main", "-c", btclib_node_module._SUBMITPACKAGE_PROBE],
        check=False,
        capture_output=True,
    )


def test_serves_submitpackage_is_false_where_the_table_lacks_it() -> None:
    """A nonzero exit -- the RPC missing, or no such table -- is `False`."""
    btclib_node_module._serves_submitpackage.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._serves_submitpackage("fake-python-release") is False


@pytest.mark.parametrize(
    "callbacks, served",
    [
        ('{"submitpackage": None}', True),
        ('{"getblockcount": None}', False),
        ('{"getblockcount": "submitpackage"}', False),
        ("[]", False),
    ],
)
def test_submitpackage_probe_answers_from_the_table_s_keys(
    callbacks: str, served: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_SUBMITPACKAGE_PROBE` answers from the keys of a stub `callbacks`."""
    package = tmp_path / "btclib_node" / "rpc"
    package.mkdir(parents=True)
    (tmp_path / "btclib_node" / "__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "callbacks.py").write_text(f"callbacks = {callbacks}\n")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._serves_submitpackage.cache_clear()
    answer = btclib_node_module._serves_submitpackage(sys.executable)
    btclib_node_module._serves_submitpackage.cache_clear()
    assert answer is served


def test_serves_getorphantxs_reads_the_probe_s_own_return_code() -> None:
    """`_serves_getorphantxs` is `_GETORPHANTXS_PROBE` exiting zero."""
    btclib_node_module._serves_getorphantxs.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._serves_getorphantxs("fake-python-main") is True
    run.assert_called_once_with(
        ["fake-python-main", "-c", btclib_node_module._GETORPHANTXS_PROBE],
        check=False,
        capture_output=True,
    )


def test_serves_getorphantxs_is_false_where_the_table_lacks_it() -> None:
    """A nonzero exit -- the RPC missing, or no such table -- is `False`."""
    btclib_node_module._serves_getorphantxs.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._serves_getorphantxs("fake-python-release") is False


@pytest.mark.parametrize(
    "callbacks, served",
    [
        ('{"getorphantxs": None}', True),
        ('{"getblockcount": None}', False),
        ('{"getblockcount": "getorphantxs"}', False),
        ("[]", False),
    ],
)
def test_getorphantxs_probe_answers_from_the_table_s_keys(
    callbacks: str, served: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_GETORPHANTXS_PROBE` answers from the keys of a stub `callbacks`."""
    package = tmp_path / "btclib_node" / "rpc"
    package.mkdir(parents=True)
    (tmp_path / "btclib_node" / "__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "callbacks.py").write_text(f"callbacks = {callbacks}\n")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._serves_getorphantxs.cache_clear()
    answer = btclib_node_module._serves_getorphantxs(sys.executable)
    btclib_node_module._serves_getorphantxs.cache_clear()
    assert answer is served


def test_binds_address_reads_the_probe_s_own_return_code() -> None:
    """`_binds_address` is `_BIND_PROBE` exiting zero."""
    btclib_node_module._binds_address.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._binds_address("fake-python-main") is True
    _assert_probed_in_own_home(run, "fake-python-main", btclib_node_module._BIND_PROBE)


def test_binds_address_is_false_where_the_parse_refuses() -> None:
    """A nonzero exit -- the flag refused -- is `False`."""
    btclib_node_module._binds_address.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._binds_address("fake-python-release") is False


def test_sets_min_relay_fee_reads_the_probe_s_own_return_code() -> None:
    """`_sets_min_relay_fee` is `_MIN_RELAY_FEE_PROBE` exiting zero."""
    btclib_node_module._sets_min_relay_fee.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._sets_min_relay_fee("fake-python-1332") is True
    _assert_probed_in_own_home(
        run, "fake-python-1332", btclib_node_module._MIN_RELAY_FEE_PROBE
    )


def test_sets_min_relay_fee_is_false_where_the_parse_refuses() -> None:
    """A nonzero exit -- the flag refused, or a rate misread -- is `False`."""
    btclib_node_module._sets_min_relay_fee.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._sets_min_relay_fee("fake-python-pre-1332") is False


def test_permits_bare_multisig_reads_the_probe_s_own_return_code() -> None:
    """`_permits_bare_multisig` is `_BARE_MULTISIG_PROBE` exiting zero."""
    btclib_node_module._permits_bare_multisig.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._permits_bare_multisig("fake-python-1497") is True
    _assert_probed_in_own_home(
        run, "fake-python-1497", btclib_node_module._BARE_MULTISIG_PROBE
    )


def test_permits_bare_multisig_is_false_where_the_parse_refuses() -> None:
    """A nonzero exit -- the flag refused or its value misread -- is `False`."""
    btclib_node_module._permits_bare_multisig.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert (
            btclib_node_module._permits_bare_multisig("fake-python-pre-1497") is False
        )


def _run_probe_on_stub_config(
    fn: _lru_cache_wrapper[bool],
    body: str,
    tmp_path: Path,
    mp: pytest.MonkeyPatch,
) -> bool:
    """Run `fn` against a `btclib_node.cli.build_config` stub with `body`."""
    package = tmp_path / "btclib_node"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text(
        f"from types import SimpleNamespace\ndef build_config(argv):\n    {body}\n"
    )
    mp.setenv("PYTHONPATH", str(tmp_path))
    fn.cache_clear()
    answer = fn(sys.executable)
    fn.cache_clear()
    return answer


@pytest.mark.parametrize(
    "body, binds",
    [
        ('return SimpleNamespace(bind=("127.0.0.1:18555",))', True),
        ("return SimpleNamespace(bind=())", False),
        ("return SimpleNamespace()", False),
        ("raise SystemExit(2)", False),
    ],
)
def test_bind_probe_answers_from_the_parsed_config(
    body: str, binds: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_BIND_PROBE` answers from `bind` on a stub `build_config`."""
    answer = _run_probe_on_stub_config(
        btclib_node_module._binds_address, body, tmp_path, monkeypatch
    )
    assert answer is binds


@pytest.mark.parametrize(
    "body, sets",
    [
        (
            "return SimpleNamespace(min_relay_feerate=SimpleNamespace(sats_per_kvbyte=10))",
            True,
        ),
        (
            "return SimpleNamespace(min_relay_feerate=SimpleNamespace(sats_per_kvbyte=1000))",
            False,
        ),
        ("return SimpleNamespace()", False),
        ("raise SystemExit(2)", False),
    ],
)
def test_min_relay_fee_probe_answers_from_the_parsed_config(
    body: str, sets: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_MIN_RELAY_FEE_PROBE` answers from `min_relay_feerate` on a stub."""
    answer = _run_probe_on_stub_config(
        btclib_node_module._sets_min_relay_fee, body, tmp_path, monkeypatch
    )
    assert answer is sets


@pytest.mark.parametrize(
    "body, permits_off",
    [
        ("return SimpleNamespace(permit_bare_multisig=False)", True),
        ("return SimpleNamespace(permit_bare_multisig=True)", False),
        ("return SimpleNamespace()", False),
        ("raise SystemExit(2)", False),
    ],
)
def test_bare_multisig_probe_answers_from_the_parsed_config(
    body: str, permits_off: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_BARE_MULTISIG_PROBE` answers from `permit_bare_multisig` on a stub."""
    answer = _run_probe_on_stub_config(
        btclib_node_module._permits_bare_multisig, body, tmp_path, monkeypatch
    )
    assert answer is permits_off


def test_speaks_v2_reads_the_probe_s_own_return_code() -> None:
    """`_speaks_v2` is `_V2_PROBE` exiting zero."""
    btclib_node_module._speaks_v2.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._speaks_v2("fake-python-1675") is True
    _assert_probed_in_own_home(run, "fake-python-1675", btclib_node_module._V2_PROBE)


def test_speaks_v2_is_false_where_the_parse_refuses() -> None:
    """A nonzero exit -- the flag refused, or left on -- is `False`."""
    btclib_node_module._speaks_v2.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._speaks_v2("fake-python-pre-1675") is False


@pytest.mark.parametrize(
    "body, speaks",
    [
        ("return SimpleNamespace(v2transport=False)", True),
        ("return SimpleNamespace(v2transport=True)", False),
        ("return SimpleNamespace()", False),
        ("raise SystemExit(2)", False),
    ],
)
def test_v2_probe_answers_from_the_parsed_config(
    body: str, speaks: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_V2_PROBE` answers from `v2transport` on a stub `build_config`."""
    package = tmp_path / "btclib_node"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text(
        f"from types import SimpleNamespace\ndef build_config(argv):\n    {body}\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._speaks_v2.cache_clear()
    answer = btclib_node_module._speaks_v2(sys.executable)
    btclib_node_module._speaks_v2.cache_clear()
    assert answer is speaks


def test_accepts_v1transport_reads_the_probe_s_own_return_code() -> None:
    """`_accepts_v1transport` is `_V1_PROBE` exiting zero."""
    btclib_node_module._accepts_v1transport.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0)) as run:
        assert btclib_node_module._accepts_v1transport("fake-python-f1") is True
    _assert_probed_in_own_home(run, "fake-python-f1", btclib_node_module._V1_PROBE)


def test_accepts_v1transport_is_false_where_the_parse_refuses() -> None:
    """A nonzero exit -- the flag refused, or read false -- is `False`."""
    btclib_node_module._accepts_v1transport.cache_clear()
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=1)):
        assert btclib_node_module._accepts_v1transport("fake-python-pre-f1") is False


@pytest.mark.parametrize(
    "body, accepts",
    [
        ("return SimpleNamespace(v1transport=True)", True),
        ("return SimpleNamespace(v1transport=False)", False),
        ("return SimpleNamespace()", False),
        ("raise SystemExit(2)", False),
    ],
)
def test_v1_probe_answers_from_the_parsed_config(
    body: str, accepts: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_V1_PROBE` answers from `v1transport` on a stub `build_config`."""
    package = tmp_path / "btclib_node"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "cli.py").write_text(
        f"from types import SimpleNamespace\ndef build_config(argv):\n    {body}\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    btclib_node_module._accepts_v1transport.cache_clear()
    answer = btclib_node_module._accepts_v1transport(sys.executable)
    btclib_node_module._accepts_v1transport.cache_clear()
    assert answer is accepts


@pytest.mark.parametrize("chain", ["regtest", "signet"])
def test_command_adds_v1transport_where_the_build_accepts_it(
    tmp_path: Path, chain: str
) -> None:
    """`-v1transport=1` is in the argv of a build with the flag, once."""
    with patch.object(btclib_node_module, "_accepts_v1transport", return_value=True):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444, chain=chain)
        command = adapter._command()
    assert command.count("-v1transport=1") == 1


def test_command_adds_nothing_where_the_build_lacks_v1transport(
    tmp_path: Path,
) -> None:
    """A build without the flag, which would refuse it, is started as before."""
    with patch.object(btclib_node_module, "_accepts_v1transport", return_value=False):
        adapter = BtclibNodeAdapter(sys.executable, tmp_path, 18443, 18444)
        command = adapter._command()
    assert not any("v1transport" in arg for arg in command)


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
