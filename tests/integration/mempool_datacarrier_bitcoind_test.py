# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_datacarrier`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_datacarrier.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the option and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-datacarrier` and `-datacarriersize` (`Capability.DATACARRIER`) gate
whether, and how large, an `OP_RETURN` output is relayed, and
`MiniWallet.create_self_transfer` (`Capability.MINE`) is what funds the
transaction that carries one, `mini_wallet.py`'s own
`nulldata_script_pub_key` building the output itself -- unlike
`ScriptPubKey.nulldata`, refusing no length, since a size limit is
exactly what a node's own `-datacarriersize` is being asked about here.

A smaller claim than Core's own file: kept are the default (uncapped)
setting, `-datacarrier=0` (no relay of any nulldata output, whatever its
size), a custom `-datacarriersize` at its own boundary, and the default
`permitbaremultisig` that `getmempoolinfo` reports, which Core's own file
checks here "rather than create a new test for it"; dropped is
Core's own fourth node (`-datacarriersize=2`) and its own full sweep of
`None`/zero-byte/one-byte payloads across every node, none of which
exercises a boundary the first three configurations do not already
cover.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx import TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, nulldata_script_pub_key
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# Core's own historical default -datacarriersize, "now used to test
# coverage" (its own file's comment) rather than any longer the default
_CUSTOM_DATACARRIER_SIZE = 83


def _start_adapter(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    extra_args: tuple[str, ...] = (),
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=extra_args,
    )
    adapter.start()
    return adapter


def test_default_settings_allow_a_large_op_return(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """With no `-datacarrier*` argument, a sizeable payload still relays."""
    require(Capability.DATACARRIER, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        tx = wallet.create_self_transfer()
        tx.vout.append(TxOut(0, nulldata_script_pub_key(b"\xaa" * 500)))
        adapter.rpc.call(
            "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
        )
        assert tx.id.hex() in adapter.rpc.call("getrawmempool")
    finally:
        adapter.stop()


def test_datacarrier_disabled_refuses_any_null_data_output(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """`-datacarrier=0` refuses relay of a null-data output of any size."""
    require(Capability.DATACARRIER, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(
        make_adapter, bitcoind_path, tmp_path, extra_args=("-datacarrier=0",)
    )
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        tx = wallet.create_self_transfer()
        tx.vout.append(TxOut(0, nulldata_script_pub_key(b"")))
        with pytest.raises(RpcError, match="datacarrier"):
            adapter.rpc.call(
                "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
            )
    finally:
        adapter.stop()


def test_datacarriersize_bounds_the_payload(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A payload at the configured size relays; one byte more is refused."""
    require(Capability.DATACARRIER, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(
        make_adapter,
        bitcoind_path,
        tmp_path,
        extra_args=(
            "-datacarrier=1",
            f"-datacarriersize={_CUSTOM_DATACARRIER_SIZE}",
        ),
    )
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        assert (
            adapter.rpc.call("getmempoolinfo")["maxdatacarriersize"]
            == _CUSTOM_DATACARRIER_SIZE
        )

        # OP_RETURN (1) + one-byte pushdata length (2) + data
        at_limit = wallet.create_self_transfer()
        at_limit.vout.append(
            TxOut(0, nulldata_script_pub_key(b"\xbb" * (_CUSTOM_DATACARRIER_SIZE - 3)))
        )
        adapter.rpc.call(
            "sendrawtransaction",
            [at_limit.serialize(True, check_validity=False).hex()],
        )
        assert at_limit.id.hex() in adapter.rpc.call("getrawmempool")

        over_limit = wallet.create_self_transfer()
        over_limit.vout.append(
            TxOut(0, nulldata_script_pub_key(b"\xbb" * (_CUSTOM_DATACARRIER_SIZE - 2)))
        )
        with pytest.raises(RpcError, match="datacarrier"):
            adapter.rpc.call(
                "sendrawtransaction",
                [over_limit.serialize(True, check_validity=False).hex()],
            )
    finally:
        adapter.stop()


def test_bare_multisig_is_permitted_by_default(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """With no `-permitbaremultisig`, `getmempoolinfo` reports it permitted."""
    require(Capability.PERMIT_BARE_MULTISIG, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        info = adapter.rpc.call("getmempoolinfo")
        assert isinstance(info, dict)
        assert info["permitbaremultisig"] is True
    finally:
        adapter.stop()
