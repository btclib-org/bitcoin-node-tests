# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_cluster`, one body over either node.

Read from Core's `test/functional/mempool_cluster.py` (`659671ac3db7`,
2026-06-04): the mempool groups the transactions its spends connect
into clusters, reports each one linearized into chunks, and refuses a
transaction, a replacement or a package that would take a cluster past
`-limitclustercount` transactions or `-limitclustersize` kilo-vbytes.

Core's `run_test` is the body, in its own order, over one node, and
every assertion of Core's own is kept:

- `test_getmempoolcluster`: `getmempoolcluster` refuses a transaction
  the mempool does not hold, and reports a cluster's weight, its count
  and its chunks, one chunk where each child pays more than its parent
  and one per transaction where each pays less, until a
  `prioritisetransaction` makes the last one pay enough to join the
  chunk before it; `getmempoolinfo` reports the ordering optimal;
- `test_cluster_limit_rbf`, at Core's own default count: a transaction
  merging clusters is taken where the children it replaces leave the
  merged cluster within the count, and so is a package whose parent
  replaces every transaction it conflicts with;
- `test_cluster_size_limit` and `test_cluster_merging_size`, the node
  restarted under each of Core's own `-limitclustersize` values
  (`Capability.LIMIT_CLUSTER_SIZE`): a transaction, a replacement and a
  merger taking a cluster past the size are refused `too-large-cluster`,
  and a replacement keeping its size and a smaller transaction are
  taken;
- `test_cluster_count_limit` and `test_cluster_merging`, restarted
  under each of Core's own `-limitclustercount` values
  (`Capability.LIMIT_CLUSTER_COUNT`): a transaction, a replacement, a
  package and a merger taking a cluster past the count are refused
  `too-large-cluster`, a package's parent entering without its child,
  and a replacement or a package replacing as many transactions as it
  adds is taken, as is a spend of each cluster apart; every
  `getmempoolfeeratediagram` point pays no more per weight than the one
  before it.

`getmempoolcluster`, `getmempoolfeeratediagram` and `getmempoolinfo`'s
`optimal` are `Capability.CLUSTER_LINEARIZATION`'s, asked for after
both options' own capabilities, and `submitpackage` is
`Capability.PACKAGE_ACCEPTANCE`'s, asked for after it and ahead of
`Capability.MINE`.

What differs from Core's file:

- the chain is mined here by `MiniWallet` (`mini_wallet.py`), to Core's
  own count of blocks on a fresh chain rather than on top of the one
  Core's framework caches;
- a block Core's node mines from its own mempool, in the `cleanup`
  decorator, is built here client-side, carrying every transaction the
  mempool holds: `MiniWallet.generate`'s own `confirm`. Core's
  `rescan_utxos` then rebuilds its wallet's coins from the UTXO set;
  `_mine_mempool` drops, from `MiniWallet`'s own cache, every coin no
  block holds, a coin a replaced transaction paid among them;
- Core's `MiniWallet` returns a dictionary for each transaction it
  builds, its fee in BTC; `_Sent` here carries the transaction, its
  fee in satoshis and its first output. Every fee and fee rate Core
  writes in BTC is written here in satoshis, and a fee the node answers
  in BTC is converted to satoshis before it is compared.

`mempool_cluster_bitcoind_test.py` and
`mempool_cluster_btclib_node_test.py` run the body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.amount import sats_from_btc
from btclib.tx import Tx

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import DEFAULT_FEE_RATE, FEE, MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.mini_wallet import Utxo
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["mempool_limits_clusters_and_reports_their_chunks"]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's own `run_test`: the blocks its wallet mines before the first test
_CHAIN_HEIGHT = 400

# Core's own `DEFAULT_CLUSTER_LIMIT` and `DEFAULT_CLUSTER_SIZE_LIMIT_KVB`
# (`test/functional/test_framework/mempool_util.py`)
_DEFAULT_CLUSTER_LIMIT = 64
_DEFAULT_CLUSTER_SIZE_LIMIT_KVB = 101

# Core's own `run_test`: the values each option is restarted with
_CLUSTER_SIZE_LIMITS_KVB = (10, 20, 33, 100, _DEFAULT_CLUSTER_SIZE_LIMIT_KVB)
_CLUSTER_COUNT_LIMITS = (4, 10, 16, 32, _DEFAULT_CLUSTER_LIMIT)

# Core's own `test_cluster_merging`: the count merging is only tested past
_MERGING_COUNT_FLOOR = 10

# Core's own `test_cluster_merging`: the first cluster's own sizes
_FIRST_CLUSTER_COUNTS = (1, 5, 10)

# Core's own `test_cluster_size_limit` and `test_cluster_merging_size`:
# the transactions a cluster is built from, fewer than the count limit
_SIZE_TEST_TXS = 10

# Core's own: the vbytes left free for a reasonably sized transaction
_SIZE_BUFFER = 500

# Core's own: how far past, and short of, the vbytes left a transaction is
_SIZE_MARGIN = 4

# Core's own `test_limit_enforcement`: the replaced transaction's fee,
# `Decimal("0.000001")` BTC, and the multiple of the fee it beats a
# replacement pays
_REPLACED_FEE = 100
_REPLACEMENT_FEE_MULTIPLE = 5

# Core's own `test_limit_enforcement`: satoshis per vbyte a sized
# replacement pays
_SIZED_REPLACEMENT_FEE_RATE = 10

# Core's own `test_limit_enforcement_package`: the multiple of the fee to
# beat the good parent pays, the bad one paying `_REPLACEMENT_FEE_MULTIPLE`
_GOOD_PARENT_FEE_MULTIPLE = 10

# Core's own `test_cluster_merging_size`: the fee per output of a merger
_MERGER_FEE_PER_OUTPUT = 10_000

# Core's own `test_getmempoolcluster`: the rates, in BTC/kvB, of the
# children paying more than their parent and of those paying less
_HIGH_FEE_RATES = (Decimal("0.01"), Decimal("0.1"))
_LOW_FEE_RATES = (Decimal("0.000002"), Decimal("0.000001"))

# Core's own `RPC_VERIFY_REJECTED` and `RPC_INVALID_ADDRESS_OR_KEY`
_RPC_VERIFY_REJECTED = -26
_RPC_INVALID_ADDRESS_OR_KEY = -5


@dataclass(frozen=True)
class _Sent:
    """What Core's `MiniWallet` returns for a transaction it builds.

    `tx` is Core's `tx`, `fee` its `fee` in satoshis rather than BTC, and
    `new_utxo` its `new_utxo`, the first output.
    """

    tx: Tx
    fee: int
    new_utxo: Utxo

    @property
    def txid(self) -> str:
        """Return the transaction's own txid, as the RPC spells it."""
        return self.tx.id.hex()


def _hex(tx: Tx) -> str:
    """Return `tx` serialized with its witness, `sendrawtransaction`'s form."""
    return tx.serialize(True, check_validity=False).hex()


def _mempool(node: NodeAdapter) -> list[str]:
    """Return the txids `node`'s own `getrawmempool` answers."""
    txids = node.rpc.call("getrawmempool")
    assert isinstance(txids, list)
    return txids


def _sent(wallet: MiniWallet, tx: Tx, spent: Sequence[Utxo]) -> _Sent:
    """Return `tx`, which spends `spent`, with its fee and first output."""
    fee = sum(utxo.value for utxo in spent) - sum(out.value for out in tx.vout)
    return _Sent(tx, fee, wallet.new_utxos(tx)[0])


def _create(
    wallet: MiniWallet,
    utxo: Utxo,
    *,
    fee: int = 0,
    target_vsize: int = 0,
    locktime: int = 0,
) -> _Sent:
    """Core's `create_self_transfer`, spending `utxo`."""
    tx = wallet.create_self_transfer(
        utxo_to_spend=utxo, fee=fee, target_vsize=target_vsize, locktime=locktime
    )
    return _sent(wallet, tx, [utxo])


def _send(
    wallet: MiniWallet,
    utxo: Utxo,
    *,
    fee_rate: int = DEFAULT_FEE_RATE,
    target_vsize: int = 0,
) -> _Sent:
    """Core's `send_self_transfer`, spending `utxo`."""
    tx = wallet.send_self_transfer(
        utxo_to_spend=utxo, fee_rate=fee_rate, target_vsize=target_vsize
    )
    return _sent(wallet, tx, [utxo])


def _create_multi(
    wallet: MiniWallet,
    utxos: Sequence[Utxo],
    *,
    fee_per_output: int = FEE,
    target_vsize: int = 0,
) -> _Sent:
    """Core's `create_self_transfer_multi`, spending `utxos`."""
    tx = wallet.create_self_transfer_multi(
        utxos_to_spend=utxos, fee_per_output=fee_per_output, target_vsize=target_vsize
    )
    return _sent(wallet, tx, utxos)


def _assert_too_large_cluster(node: NodeAdapter, tx: Tx) -> None:
    """Check `node` refuses `tx` `too-large-cluster`."""
    with pytest.raises(RpcError, match="too-large-cluster") as refused:
        node.rpc.call("sendrawtransaction", [_hex(tx)])
    assert refused.value.code == _RPC_VERIFY_REJECTED


def _cluster_info(node: NodeAdapter, txid: str) -> dict[str, object]:
    """Return `getmempoolcluster`'s answer for `txid`, fees in satoshis."""
    info = node.rpc.call("getmempoolcluster", [txid])
    assert isinstance(info, dict)
    for chunk in info["chunks"]:
        chunk["chunkfee"] = sats_from_btc(chunk["chunkfee"])
    return info


def _chunk(*sent: _Sent, fee: int | None = None) -> dict[str, object]:
    """Return the chunk `getmempoolcluster` reports for `sent`, in order."""
    return {
        "chunkfee": sum(s.fee for s in sent) if fee is None else fee,
        "chunkweight": sum(s.tx.weight for s in sent),
        "txs": [s.txid for s in sent],
    }


def _mine_mempool(node: NodeAdapter, wallet: MiniWallet) -> None:
    """Core's `cleanup` decorator: mine the mempool, then refresh the coins.

    Each block carries every transaction the mempool holds, a parent
    ahead of each child `getrawmempool`'s own `depends` names. Then every
    coin of `wallet`'s own cache that no block holds is dropped: with
    the mempool empty, no transaction pays it any more.
    """
    while entries := node.rpc.call("getrawmempool", [True]):
        assert isinstance(entries, dict)
        ordered: list[str] = []
        while len(ordered) < len(entries):
            ordered += [
                txid
                for txid, entry in entries.items()
                if txid not in ordered and set(entry["depends"]) <= set(ordered)
            ]
        txs = [
            Tx.parse(
                bytes.fromhex(node.rpc.call("getrawtransaction", [txid])),
                check_validity=False,
            )
            for txid in ordered
        ]
        wallet.generate(1, confirm=txs)
    for utxo in wallet.get_utxos(mark_as_spent=False, include_immature_coinbase=True):
        if not utxo.confirmed:
            wallet.get_utxo(txid=utxo.outpoint.tx_id.hex(), vout=utxo.outpoint.vout)


def _add_chain_cluster(
    node: NodeAdapter, wallet: MiniWallet, cluster_count: int, target_vsize: int = 0
) -> list[_Sent]:
    """Core's `add_chain_cluster`: a chain of `cluster_count` transactions."""
    parent = _send(
        wallet, wallet.get_utxo(confirmed_only=True), target_vsize=target_vsize
    )
    all_txids = [parent.txid]
    all_results = [parent]
    utxo_to_spend = parent.new_utxo

    while len(all_results) < cluster_count:
        next_tx = _send(wallet, utxo_to_spend, target_vsize=target_vsize)
        assert next_tx.txid in _mempool(node)

        # each transaction is in the same cluster as the first
        assert node.rpc.call("getmempoolcluster", [next_tx.txid]) == node.rpc.call(
            "getmempoolcluster", [parent.txid]
        )

        # the ancestors are what Core expects
        ancestors = node.rpc.call("getmempoolancestors", [next_tx.txid])
        assert sorted(ancestors) == sorted(all_txids)

        # each successive transaction is added as a descendant
        assert all(
            next_tx.txid in node.rpc.call("getmempooldescendants", [txid])
            for txid in all_txids
        )

        all_results.append(next_tx)
        all_txids.append(next_tx.txid)
        utxo_to_spend = next_tx.new_utxo

    info = node.rpc.call("getmempoolcluster", [parent.txid])
    assert info["txcount"] == cluster_count
    return all_results


def _check_feerate_diagram(node: NodeAdapter) -> None:
    """Core's `check_feerate_diagram`: a sanity check of the diagram."""
    diagram = node.rpc.call("getmempoolfeeratediagram")
    assert isinstance(diagram, list)
    last_weight, last_fee = 0, 0
    for point in diagram:
        weight, fee = point["weight"], sats_from_btc(point["fee"])
        # the weight is always positive, except for the first point
        assert weight > 0 or fee == 0
        # monotonically decreasing fee per weight
        assert last_fee * weight >= fee * last_weight
        last_weight, last_fee = weight, fee


def _limit_enforcement(
    node: NodeAdapter,
    wallet: MiniWallet,
    cluster_submitted: list[_Sent],
    target_vsize_per_tx: int = 0,
) -> None:
    """Core's `test_limit_enforcement`, mutating `cluster_submitted`."""
    assert len(cluster_submitted) >= 3
    last_result = cluster_submitted[-1]

    # one more transaction in the cluster is refused
    bad_tx = _create(wallet, last_result.new_utxo, target_vsize=target_vsize_per_tx)
    _assert_too_large_cluster(node, bad_tx.tx)

    # and so is a replacement taking the cluster past the limit
    utxo_to_double_spend = wallet.get_utxo(confirmed_only=True)
    tx_to_replace = _create(wallet, utxo_to_double_spend, fee=_REPLACED_FEE)
    node.rpc.call("sendrawtransaction", [_hex(tx_to_replace.tx)])

    fee_to_use = (
        target_vsize_per_tx * _SIZED_REPLACEMENT_FEE_RATE
        if target_vsize_per_tx
        else _REPLACED_FEE * _REPLACEMENT_FEE_MULTIPLE
    )
    bad_tx_also_replacement = _create_multi(
        wallet,
        [last_result.new_utxo, utxo_to_double_spend],
        target_vsize=target_vsize_per_tx,
        fee_per_output=fee_to_use,
    )
    _assert_too_large_cluster(node, bad_tx_also_replacement.tx)

    # replacing the last transaction removes one as it adds one, and the
    # vsize cancels out the same way
    second_to_last_utxo = cluster_submitted[-2].new_utxo
    fee_to_beat = cluster_submitted[-1].fee
    vsize_to_use = cluster_submitted[-1].tx.vsize if target_vsize_per_tx else 0
    good_tx_replacement = _create(
        wallet,
        second_to_last_utxo,
        fee=fee_to_beat * _REPLACEMENT_FEE_MULTIPLE,
        target_vsize=vsize_to_use,
    )
    node.rpc.call("sendrawtransaction", [_hex(good_tx_replacement.tx), 0])

    cluster_submitted[-1] = good_tx_replacement


def _limit_enforcement_package(
    node: NodeAdapter, wallet: MiniWallet, cluster_submitted: list[_Sent]
) -> None:
    """Core's `test_limit_enforcement_package`."""
    # a package from the second to last transaction adds two and removes
    # one, past the limit
    last_utxo = cluster_submitted[-2].new_utxo
    fee_to_beat = cluster_submitted[-1].fee
    parent_tx_bad = _create(
        wallet, last_utxo, fee=fee_to_beat * _REPLACEMENT_FEE_MULTIPLE
    )
    child_tx_bad = _create(wallet, parent_tx_bad.new_utxo)
    # the parent is taken, and the child refused
    result_parent_only = node.rpc.call(
        "submitpackage", [[_hex(parent_tx_bad.tx), _hex(child_tx_bad.tx)]]
    )

    assert parent_tx_bad.txid in _mempool(node)
    assert child_tx_bad.txid not in _mempool(node)
    assert result_parent_only["package_msg"] == "transaction failed"
    child_result = result_parent_only["tx-results"][child_tx_bad.tx.hash.hex()]
    assert child_result["error"] == "too-large-cluster"
    replaced = result_parent_only["replaced-transactions"]
    assert replaced == [cluster_submitted[-1].txid]

    # a package from the third to last transaction adds two and removes
    # two, within the limit; a locktime of its own keeps the parent from
    # being the transaction it replaces
    third_to_last_utxo = cluster_submitted[-3].new_utxo
    parent_tx_good = _create(
        wallet,
        third_to_last_utxo,
        locktime=1,
        fee=fee_to_beat * _GOOD_PARENT_FEE_MULTIPLE,
    )
    child_tx_good = _create(wallet, parent_tx_good.new_utxo)
    assert parent_tx_good.txid != cluster_submitted[-2].txid
    assert child_tx_good.txid != parent_tx_bad.txid
    result_both_good = node.rpc.call(
        "submitpackage", [[_hex(parent_tx_good.tx), _hex(child_tx_good.tx)], 0]
    )
    assert result_both_good["package_msg"] == "success"
    assert parent_tx_good.txid in _mempool(node)
    assert child_tx_good.txid in _mempool(node)
    assert set(result_both_good["replaced-transactions"]) == {
        parent_tx_bad.txid,
        cluster_submitted[-2].txid,
    }


def _cluster_count_limit(
    node: NodeAdapter, wallet: MiniWallet, max_cluster_count: int
) -> None:
    """Core's `test_cluster_count_limit`."""
    cluster_submitted = _add_chain_cluster(node, wallet, max_cluster_count)
    _check_feerate_diagram(node)
    for result in cluster_submitted:
        info = node.rpc.call("getmempoolcluster", [result.txid])
        assert info["txcount"] == max_cluster_count

    _limit_enforcement(node, wallet, cluster_submitted)
    _limit_enforcement_package(node, wallet, cluster_submitted)
    _mine_mempool(node, wallet)


def _cluster_size_limit(
    node: NodeAdapter, wallet: MiniWallet, max_cluster_size_vbytes: int
) -> None:
    """Core's `test_cluster_size_limit`."""
    target_vsize_per_tx = (max_cluster_size_vbytes - _SIZE_BUFFER) // _SIZE_TEST_TXS
    cluster_submitted = _add_chain_cluster(
        node, wallet, _SIZE_TEST_TXS, target_vsize_per_tx
    )

    info = node.rpc.call("getmempoolcluster", [cluster_submitted[0].txid])
    # the weight in vbytes, rounded up
    vsize_remaining = max_cluster_size_vbytes - (info["clusterweight"] + 3) // 4
    _limit_enforcement(
        node,
        wallet,
        cluster_submitted,
        target_vsize_per_tx=vsize_remaining + _SIZE_MARGIN,
    )

    # a small transaction added to the cluster is taken
    last_result = cluster_submitted[-1]
    small_tx = _create(wallet, last_result.new_utxo, target_vsize=vsize_remaining)
    node.rpc.call("sendrawtransaction", [_hex(small_tx.tx)])
    _mine_mempool(node, wallet)


def _cluster_merging(
    node: NodeAdapter, wallet: MiniWallet, max_cluster_count: int
) -> None:
    """Core's `test_cluster_merging`."""
    for num_txns_cluster1 in _FIRST_CLUSTER_COUNTS:
        cluster1 = _add_chain_cluster(node, wallet, num_txns_cluster1)
        for result in cluster1:
            node.rpc.call("sendrawtransaction", [_hex(result.tx)])
        utxo_from_cluster1 = cluster1[-1].new_utxo

        # the second cluster holds the rest of the count
        assert max_cluster_count > num_txns_cluster1
        num_txns_cluster2 = max_cluster_count - num_txns_cluster1
        cluster2 = _add_chain_cluster(node, wallet, num_txns_cluster2)
        for result in cluster2:
            node.rpc.call("sendrawtransaction", [_hex(result.tx)])
        utxo_from_cluster2 = cluster2[-1].new_utxo

        # a spend of both merges them, past the count
        tx_merger = _create_multi(wallet, [utxo_from_cluster1, utxo_from_cluster2])
        _assert_too_large_cluster(node, tx_merger.tx)

        # a spend of each apart is taken
        tx_spending_cluster1 = _send(wallet, utxo_from_cluster1)
        tx_spending_cluster2 = _send(wallet, utxo_from_cluster2)
        assert tx_spending_cluster1.txid in _mempool(node)
        assert tx_spending_cluster2.txid in _mempool(node)

    # a spend of as many singleton clusters as the count, each spending a
    # confirmed coin so that they are distinct
    utxos_to_merge = []
    for _ in range(max_cluster_count):
        confirmed_utxo = wallet.get_utxo(confirmed_only=True)
        singleton = _send(wallet, confirmed_utxo)
        assert singleton.txid in _mempool(node)
        utxos_to_merge.append(singleton.new_utxo)

    assert len(utxos_to_merge) == max_cluster_count
    tx_merger = _create_multi(wallet, utxos_to_merge)
    _assert_too_large_cluster(node, tx_merger.tx)

    # one cluster fewer is taken
    tx_merger_all_but_one = _create_multi(wallet, utxos_to_merge[:-1])
    node.rpc.call("sendrawtransaction", [_hex(tx_merger_all_but_one.tx)])
    assert tx_merger_all_but_one.txid in _mempool(node)
    _mine_mempool(node, wallet)


def _cluster_merging_size(
    node: NodeAdapter, wallet: MiniWallet, max_cluster_size_vbytes: int
) -> None:
    """Core's `test_cluster_merging_size`."""
    utxos_to_merge = []
    vsize_remaining = max_cluster_size_vbytes
    for _ in range(_SIZE_TEST_TXS):
        confirmed_utxo = wallet.get_utxo(confirmed_only=True)
        singleton = _send(wallet, confirmed_utxo)
        assert singleton.txid in _mempool(node)
        utxos_to_merge.append(singleton.new_utxo)
        vsize_remaining -= singleton.tx.vsize

    assert vsize_remaining >= _SIZE_BUFFER

    # a spend of every cluster past the size is refused
    tx_merger_too_big = _create_multi(
        wallet,
        utxos_to_merge,
        target_vsize=vsize_remaining + _SIZE_MARGIN,
        fee_per_output=_MERGER_FEE_PER_OUTPUT,
    )
    _assert_too_large_cluster(node, tx_merger_too_big.tx)

    # a slightly smaller one is taken
    tx_merger_small = _create_multi(
        wallet,
        utxos_to_merge[:-1],
        target_vsize=vsize_remaining - _SIZE_MARGIN,
        fee_per_output=_MERGER_FEE_PER_OUTPUT,
    )
    node.rpc.call("sendrawtransaction", [_hex(tx_merger_small.tx)])
    assert tx_merger_small.txid in _mempool(node)
    _mine_mempool(node, wallet)


def _cluster_limit_rbf(
    node: NodeAdapter, wallet: MiniWallet, max_cluster_count: int
) -> None:
    """Core's `test_cluster_limit_rbf`."""
    # the replaced transactions pay the minimum fee rate, there being many
    min_feerate = sats_from_btc(node.rpc.call("getmempoolinfo")["mempoolminfee"])

    # the cluster count takes a replacement into account
    utxos_created_by_parents = []
    fees_rbf_sats = 0
    for _ in range(max_cluster_count - 1):
        parent_tx = _send(wallet, wallet.get_utxo(confirmed_only=True))
        utxo_to_replace = parent_tx.new_utxo
        child_tx = _send(wallet, utxo_to_replace, fee_rate=min_feerate)

        fees_rbf_sats += child_tx.fee
        utxos_created_by_parents.append(utxo_to_replace)

    # a cluster of the whole count, once the children it replaces are gone
    tx_merger_replacer = _create_multi(
        wallet, utxos_created_by_parents, fee_per_output=fees_rbf_sats * 2
    )
    node.rpc.call("sendrawtransaction", [_hex(tx_merger_replacer.tx)])
    assert tx_merger_replacer.txid in _mempool(node)
    info = node.rpc.call("getmempoolcluster", [tx_merger_replacer.txid])
    assert info["txcount"] == max_cluster_count

    # and so does a package replacement
    utxos_to_replace = []
    fee_rbf = 0
    for _ in range(max_cluster_count):
        confirmed_utxo = wallet.get_utxo(confirmed_only=True)
        tx_to_replace = _send(wallet, confirmed_utxo, fee_rate=min_feerate)
        fee_rbf += tx_to_replace.fee
        utxos_to_replace.append(confirmed_utxo)

    tx_replacer = _create_multi(wallet, utxos_to_replace)
    assert tx_replacer.txid not in _mempool(node)
    tx_replacer_sponsor = _create(wallet, tx_replacer.new_utxo, fee=fee_rbf * 2)

    node.rpc.call(
        "submitpackage", [[_hex(tx_replacer.tx), _hex(tx_replacer_sponsor.tx)], 0]
    )
    assert tx_replacer.txid in _mempool(node)
    assert tx_replacer_sponsor.txid in _mempool(node)
    info = node.rpc.call("getmempoolcluster", [tx_replacer.txid])
    assert info["txcount"] == 2
    _mine_mempool(node, wallet)


def _getmempoolcluster(node: NodeAdapter, wallet: MiniWallet) -> None:
    """Core's `test_getmempoolcluster`."""
    assert _mempool(node) == []

    # the key is there, and trivially optimal
    assert node.rpc.call("getmempoolinfo")["optimal"] is True

    # a transaction the mempool does not hold
    not_mempool_tx = wallet.create_self_transfer()
    with pytest.raises(RpcError, match="Transaction not in mempool") as refused:
        node.rpc.call("getmempoolcluster", [not_mempool_tx.id.hex()])
    assert refused.value.code == _RPC_INVALID_ADDRESS_OR_KEY

    # the chunks are recomputed: each child paying more than its parent
    # joins its chunk
    first = _send(wallet, wallet.get_utxo())
    expected = {
        "clusterweight": first.tx.weight,
        "txcount": 1,
        "chunks": [_chunk(first)],
    }
    assert _cluster_info(node, first.txid) == expected

    # an unconnected transaction changes nothing
    _send(wallet, wallet.get_utxo())
    assert _cluster_info(node, first.txid) == expected

    chain = [first]
    for fee_rate in _HIGH_FEE_RATES:
        chain.append(
            _send(wallet, chain[-1].new_utxo, fee_rate=sats_from_btc(fee_rate))
        )
        info = _cluster_info(node, first.txid)
        # the answer is the same across the cluster's own transactions
        assert info == _cluster_info(node, chain[-1].txid)
        assert info == {
            "clusterweight": sum(s.tx.weight for s in chain),
            "txcount": len(chain),
            "chunks": [_chunk(*chain)],
        }

    # each child paying less than its parent is a chunk of its own
    first = _send(wallet, wallet.get_utxo())
    assert _cluster_info(node, first.txid) == {
        "clusterweight": first.tx.weight,
        "txcount": 1,
        "chunks": [_chunk(first)],
    }
    chain = [first]
    for fee_rate in _LOW_FEE_RATES:
        chain.append(
            _send(wallet, chain[-1].new_utxo, fee_rate=sats_from_btc(fee_rate))
        )
        info = _cluster_info(node, first.txid)
        assert info == _cluster_info(node, chain[-1].txid)
        assert info == {
            "clusterweight": sum(s.tx.weight for s in chain),
            "txcount": len(chain),
            "chunks": [_chunk(s) for s in chain],
        }

    # known optimality directly after a submission
    assert node.rpc.call("getmempoolinfo")["optimal"] is True

    # prioritised, the last transaction joins the second one's chunk
    _, second, third = chain
    node.rpc.call("prioritisetransaction", [third.txid, 0, third.fee + 1])
    assert _cluster_info(node, first.txid) == {
        "clusterweight": sum(s.tx.weight for s in chain),
        "txcount": len(chain),
        "chunks": [
            _chunk(first),
            _chunk(second, third, fee=second.fee + 2 * third.fee + 1),
        ],
    }
    _mine_mempool(node, wallet)


def mempool_limits_clusters_and_reports_their_chunks(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.LIMIT_CLUSTER_SIZE, node.capabilities, skip_counts)
    require(Capability.LIMIT_CLUSTER_COUNT, node.capabilities, skip_counts)
    require(Capability.CLUSTER_LINEARIZATION, node.capabilities, skip_counts)
    require(Capability.PACKAGE_ACCEPTANCE, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(_CHAIN_HEIGHT)

    _getmempoolcluster(node, wallet)

    _cluster_limit_rbf(node, wallet, _DEFAULT_CLUSTER_LIMIT)

    for cluster_size_limit_kvb in _CLUSTER_SIZE_LIMITS_KVB:
        node.restart([f"-limitclustersize={cluster_size_limit_kvb}"])
        cluster_size_limit = cluster_size_limit_kvb * 1000
        _cluster_size_limit(node, wallet, cluster_size_limit)
        _cluster_merging_size(node, wallet, cluster_size_limit)

    for cluster_count_limit in _CLUSTER_COUNT_LIMITS:
        node.restart([f"-limitclustercount={cluster_count_limit}"])
        _cluster_count_limit(node, wallet, cluster_count_limit)
        if cluster_count_limit > _MERGING_COUNT_FLOOR:
            _cluster_merging(node, wallet, cluster_count_limit)
