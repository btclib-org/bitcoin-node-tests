# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_limits`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_package_limits.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the option and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-limitclustercount` (`Capability.LIMIT_CLUSTER_COUNT`) caps how many
transactions one mempool cluster may hold, in-mempool and in-package
together, and `MiniWallet.send_self_transfer_chain` /
`create_self_transfer_multi` build the two shapes Core's own file checks
that boundary with.

A smaller claim than Core's own file: kept is one ancestor-side case
(24 in-mempool ancestors, a 2-tx package extending them, both counted
together against the cluster count) and one descendant-side case (a
top parent with two 12-transaction chains hanging off it, its own
in-mempool and in-package descendants only exceeding the limit when
counted together). Dropped is Core's own file's two further splits of
the ancestor case (2 mempool/24 package, 13/13) and its own second
descendant shape (`test_desc_count_limits_2`) -- each a different split
of a mechanism the kept case already demonstrates -- and its own
descendant-size case (`test_desc_size_limits`), which needs
`create_self_transfer_multi`'s `target_vsize` at a size large enough
(21 KvB per leg) to make a real functional-test run slow for a
boundary this file's other two cases already establish on the ancestor
and descendant *count* sides.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from btclib.tx import Tx

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_LIMIT_CLUSTER_COUNT = 25


def _start_adapter(bitcoind_path: str, tmp_path: Path) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-limitclustercount={_LIMIT_CLUSTER_COUNT}",),
    )
    adapter.start()
    return adapter


def _package_hex(txs: list[Tx]) -> list[str]:
    return [tx.serialize(True, check_validity=False).hex() for tx in txs]


def _assert_all_too_large_cluster(adapter: BitcoindAdapter, package: list[Tx]) -> None:
    results = adapter.rpc.call("testmempoolaccept", [_package_hex(package)])
    assert isinstance(results, list)
    assert len(results) == len(package)
    for result in results:
        assert "too-large-cluster" in result["package-error"], result


def _assert_all_allowed(adapter: BitcoindAdapter, package: list[Tx]) -> None:
    results = adapter.rpc.call("testmempoolaccept", [_package_hex(package)])
    assert isinstance(results, list)
    assert all(result["allowed"] for result in results), results


def test_in_package_ancestors_count_toward_the_mempool_ancestor_limit(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """24 in-mempool ancestors plus a 2-tx package exceed cluster count 25."""
    require(Capability.LIMIT_CLUSTER_COUNT, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        assert adapter.rpc.call("getmempoolinfo")["size"] == 0

        chain = wallet.send_self_transfer_chain(chain_length=24)
        assert adapter.rpc.call("getmempoolinfo")["size"] == 24
        chain_tip = wallet.get_utxo(txid=chain[-1].id.hex(), vout=0)
        parent = wallet.create_self_transfer(utxo_to_spend=chain_tip)
        parent_utxo = wallet.get_utxo(txid=parent.id.hex(), vout=0)
        child = wallet.create_self_transfer(utxo_to_spend=parent_utxo)
        package = [parent, child]

        _assert_all_too_large_cluster(adapter, package)

        adapter.mine(1)
        assert adapter.rpc.call("getmempoolinfo")["size"] == 0
        _assert_all_allowed(adapter, package)
    finally:
        adapter.stop()


def test_in_package_descendants_count_toward_the_mempool_descendant_limit(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A top parent's own descendants exceed the limit counted together.

    A top parent with two chains hanging off it, 11 and 12 transactions
    deep -- 24 in-mempool descendants including the parent itself -- and
    a package extending each chain by one more transaction: the top
    parent's own descendant count only exceeds 25 once the package's two
    transactions join the 24 already in the mempool.
    """
    require(Capability.LIMIT_CLUSTER_COUNT, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)

        top_parent = wallet.send_self_transfer_multi(num_outputs=2)
        first_leg = wallet.get_utxo(txid=top_parent.id.hex(), vout=0)
        second_leg = wallet.get_utxo(txid=top_parent.id.hex(), vout=1)
        chain_a = wallet.send_self_transfer_chain(
            chain_length=11, utxo_to_spend=first_leg
        )
        chain_b = wallet.send_self_transfer_chain(
            chain_length=12, utxo_to_spend=second_leg
        )
        assert adapter.rpc.call("getmempoolinfo")["size"] == 1 + 11 + 12

        chain_a_tip = wallet.get_utxo(txid=chain_a[-1].id.hex(), vout=0)
        chain_b_tip = wallet.get_utxo(txid=chain_b[-1].id.hex(), vout=0)
        package = [
            wallet.create_self_transfer(utxo_to_spend=chain_a_tip),
            wallet.create_self_transfer(utxo_to_spend=chain_b_tip),
        ]

        _assert_all_too_large_cluster(adapter, package)

        adapter.mine(1)
        assert adapter.rpc.call("getmempoolinfo")["size"] == 0
        _assert_all_allowed(adapter, package)
    finally:
        adapter.stop()
