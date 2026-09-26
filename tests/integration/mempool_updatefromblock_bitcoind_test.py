# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_updatefromblock`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/mempool_updatefromblock.py`
(`fa6b05c96ffb`, 2026-03-12) and narrowed to what the option and
MiniWallet families reach together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-limitclustersize` (`Capability.LIMIT_CLUSTER_SIZE`) is the one option
either kept subtest configures, and `MiniWallet.create_self_transfer_multi`
/`create_self_transfer_chain` are what build the graphs Core's own file
reorgs back into the mempool.

A smaller claim than Core's own file: kept is the acyclic-tournament
case (`transaction_graph_test`, a much smaller tournament than Core's
own `DEFAULT_CLUSTER_LIMIT`-sized one, the mechanism -- every
mempool-entry's own ancestor/descendant count and size recomputed after
a reorg re-adds every transaction a mined block once carried -- needing
no particular size to hold) and the chain-length case
(`test_chainlimits_exceeded`, unchanged: it is the node's own *default*
cluster count, not an option this file configures, that the chain has
to exceed). Dropped is Core's own `test_max_disconnect_pool_bytes`:
`MAX_DISCONNECTED_TX_POOL_BYTES` is a fixed 20-megabyte bound in
bitcoind's own C++, not a configurable option, so exercising it means
actually building, mining and reorging some twenty megabytes of
transactions -- disproportionate for a boundary neither kept subtest
needs to also cover.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import FEE, MiniWallet, build_fork
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own file reorgs a chain longer than this, exercised here at a
# fraction of Core's own DEFAULT_CLUSTER_LIMIT-sized graph: the tournament
# mechanism -- every entry's ancestor/descendant count and size recomputed
# once a reorg re-adds every transaction a mined block once carried -- does
# not need a particular size to hold
_TOURNAMENT_SIZE = 6

# bitcoind's own compiled-in default -limitclustercount, exercised by
# `test_chainlimits_exceeded` with no flag of its own: this file's only
# configured option is -limitclustersize, set high enough that the count
# default -- not the configured size -- is what the chain has to exceed
_DEFAULT_CLUSTER_LIMIT = 64


def _start_adapter(bitcoind_path: str, tmp_path: Path) -> BitcoindAdapter:
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        free_port(),
        free_port(),
        extra_args=("-limitclustersize=1000",),
    )
    adapter.start()
    return adapter


def test_reorg_recomputes_every_entry_s_own_ancestors_and_descendants(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """An acyclic tournament's own mempool entries survive a reorg intact.

    tx[K] of a `_TOURNAMENT_SIZE`-transaction tournament has
    `_TOURNAMENT_SIZE - K` descendants (itself included) and `K + 1`
    ancestors: built with some mined into blocks along the way, then
    resurrected whole by a reorg longer than any of those blocks, every
    entry's own `getmempoolentry` answer still holds.
    """
    require(Capability.LIMIT_CLUSTER_SIZE, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        # built before any tournament transaction exists, and longer than
        # however many blocks the tournament mines along the way, so that
        # submitting it later reorgs every one of them back into the mempool
        fork_blocks = build_fork(adapter, wallet.script_pub_key, 7)

        mine_after = {2, 4}
        tx_ids: list[str] = []
        tx_vsizes: list[int] = []
        for i in range(_TOURNAMENT_SIZE):
            if i == 0:
                tx = wallet.send_self_transfer_multi(
                    num_outputs=_TOURNAMENT_SIZE - 1,
                    fee_per_output=ceil(FEE / (_TOURNAMENT_SIZE - 1)),
                )
            else:
                inputs = [
                    wallet.get_utxo(txid=tx_ids[j], vout=i - j - 1) for j in range(i)
                ]
                n_outputs = _TOURNAMENT_SIZE - (i + 1) or 1
                tx = wallet.send_self_transfer_multi(
                    utxos_to_spend=inputs,
                    num_outputs=n_outputs,
                    fee_per_output=ceil(FEE / n_outputs),
                )
            tx_ids.append(tx.id.hex())
            tx_vsizes.append(tx.vsize)
            tx_count = i + 1
            if tx_count in mine_after:
                adapter.mine(1)
                assert adapter.rpc.call("getmempoolinfo")["size"] == 0

        for block in fork_blocks:
            adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
        assert adapter.rpc.call("getmempoolinfo")["size"] == _TOURNAMENT_SIZE

        for k, txid in enumerate(tx_ids):
            entry = adapter.rpc.call("getmempoolentry", [txid])
            assert entry["descendantcount"] == _TOURNAMENT_SIZE - k, (k, entry)
            assert entry["descendantsize"] == sum(tx_vsizes[k:_TOURNAMENT_SIZE]), (
                k,
                entry,
            )
            assert entry["ancestorcount"] == k + 1, (k, entry)
            assert entry["ancestorsize"] == sum(tx_vsizes[: k + 1]), (k, entry)
    finally:
        adapter.stop()


def test_a_chain_over_the_default_cluster_limit_needs_a_reorg_to_fit(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A chain longer than the default cluster count is refused entry.

    `-limitclustersize=1000` leaves the *count* default in force: a
    chain two longer than it is refused by `sendrawtransaction` one
    short of the limit, accepted into one block by `generateblock`
    naming the raw transactions directly (bypassing mempool admission
    entirely), and every transaction but the block's own last two is
    resurrected into the mempool once a longer fork reorgs that block
    away, back under the count the chain never fit unconfirmed.
    """
    require(Capability.LIMIT_CLUSTER_SIZE, BitcoindAdapter.capabilities, skip_counts)
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        fork_blocks = build_fork(adapter, wallet.script_pub_key, 10)

        chain = wallet.create_self_transfer_chain(
            chain_length=_DEFAULT_CLUSTER_LIMIT + 2
        )
        for tx in chain[:-2]:
            adapter.rpc.call(
                "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
            )
        with pytest.raises(RpcError, match="too-large-cluster"):
            adapter.rpc.call(
                "sendrawtransaction",
                [chain[-2].serialize(True, check_validity=False).hex()],
            )

        adapter.rpc.call(
            "generateblock",
            [
                "raw(42)",
                [tx.serialize(True, check_validity=False).hex() for tx in chain[:-1]],
            ],
        )
        assert adapter.rpc.call("getrawmempool") == []

        adapter.rpc.call(
            "sendrawtransaction",
            [chain[-1].serialize(True, check_validity=False).hex()],
        )

        for block in fork_blocks:
            adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
        mempool = adapter.rpc.call("getrawmempool")
        assert set(mempool) == {tx.id.hex() for tx in chain[:-2]}
    finally:
        adapter.stop()
