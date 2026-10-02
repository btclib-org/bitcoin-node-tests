# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_rbf`, as bodies over either node.

Read from Core's `test/functional/mempool_package_rbf.py` (`fa5f29774872`,
2025-12-16, the same file at the pinned `v31.1` and at Core's `master`): a
package of a parent and its child, submitted together over
`submitpackage`, replaces what its parent conflicts with in the mempool
where the package pays for it, and is refused, with the reason Core's own
file matches, where it does not -- too little absolute fee, too little
more than the replaced transactions paid to cover its own relay, a
package fee rate no higher than its parent's own, a fee rate beating no
conflict's, conflicts reaching more clusters than Core's
`MAX_REPLACEMENT_CANDIDATES`, a child with ancestors in the mempool, or a
package of more than a parent and a child.

Each of Core's subtests is a body of its own, over a fresh node whose
coins its own `MiniWallet` (`mini_wallet.py`) mines, and every assertion
of Core's own is kept. Every body asks for `Capability.PACKAGE_ACCEPTANCE`
and `Capability.MINE`; the basic body for `Capability.CONNECT` too, and
the body calling `fill_mempool` for `Capability.MAXMEMPOOL`.

What differs from Core's file:

- Core starts its nodes with `-maxmempool=5`, which only its
  `fill_mempool` needs; the mempool-ancestor body, the one calling it, is
  the one whose node restarts with it;
- that body's node restarts with a `-datacarriersize` too
  (`Capability.DATACARRIER`), over the `OP_RETURN` padding `fill_mempool`
  adds, which `v29.4` refuses by default with `scriptpubkey`
  (bitcoin/bitcoin#32406, first in `v30.0rc1`);
- Core's second node is kept by the basic body alone, whose own
  `sync_all` calls are what check that a package replacement reaches a
  peer over p2p; elsewhere Core's file reads nothing from it, the syncs
  its `generate` calls make asserting nothing about a replacement;
- Core's `MiniWallet` mines its coins once, for every subtest; here each
  body's own mines, to maturity, the coins that body spends;
- a block Core's node mines from its own mempool is built here
  client-side, carrying the transactions Core's would have taken
  (`MiniWallet.generate`'s own `confirm`); the block ending each of
  Core's subtests is not mined, each body's node being its own;
- every fee Core writes in BTC is written here in satoshis, and every
  fee rate in satoshis per 1000 virtual bytes, a refusal's own amounts
  converted back to BTC to be compared;
- `_assert_mempool_contents` is Core's `assert_mempool_contents`
  (`test/functional/test_framework/mempool_util.py`), which this
  repository's `mempool_util.py` does not carry.

`mempool_package_rbf_bitcoind_test.py` and
`mempool_package_rbf_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from btclib.amount import btc_from_sats, sats_from_btc
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mempool_util import fill_mempool
from bitcoin_node_tests.mini_wallet import PADDING_DATACARRIER_SIZE, MiniWallet
from bitcoin_node_tests.node import connect_nodes, sync_all

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.mini_wallet import Utxo
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_child_double_spending_its_mempool_ancestor_is_refused",
    "a_child_pays_to_replace_a_single_conflict",
    "a_child_pays_to_replace_its_parents_conflicts",
    "a_package_must_beat_its_direct_conflicts_feerate",
    "a_package_must_pay_more_and_for_its_own_relay",
    "a_package_replaces_no_more_clusters_than_the_limit",
    "a_package_with_mempool_ancestors_replaces_nothing",
    "a_package_with_two_parents_replaces_nothing",
    "a_zero_fee_truc_parent_and_its_child_replace_a_package",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

# Core's own `DEFAULT_FEE` (`wallet.py`), 0.0001 BTC, in satoshis
_DEFAULT_FEE = 10_000

# Core's own `DEFAULT_CHILD_FEE`: high enough to replace in each subtest
_DEFAULT_CHILD_FEE = _DEFAULT_FEE * 4

# Core's own (`messages.py`): opts into BIP125 and out of BIP68
_MAX_BIP125_RBF_SEQUENCE = 0xFFFFFFFD

# Core's own: how many clusters one replacement may conflict with, and
# before the cluster mempool (`v31.0`) how many transactions it may replace
_MAX_REPLACEMENT_CANDIDATES = 100

# Core's own `-incrementalrelayfee` default in sat/vB, the float its file
# multiplies a vsize by
_INCREMENTAL_RELAY_FEE = 0.1

# the outputs of Core's own `heavy_child`, and the vsize it stays within
_HEAVY_CHILD_OUTPUTS = 10
_HEAVY_CHILD_MAX_VSIZE = 1000

# Core's own `parent_fee_per_conflict`, in satoshis, and `child_feerate`,
# `10000 * DEFAULT_FEE` BTC/kvB, in satoshis per 1000 virtual bytes
_PARENT_FEE_PER_CONFLICT = 10_000
_CHILD_FEE_RATE = 10_000 * _DEFAULT_FEE

# what Core's own `set_test_params` starts its nodes with, for
# `fill_mempool`
_MAXMEMPOOL = "-maxmempool=5"

# what `fill_mempool`'s padding needs on a build without bitcoin/bitcoin#32406
_DATACARRIER = f"-datacarriersize={PADDING_DATACARRIER_SIZE}"


def _hex(tx: Tx) -> str:
    """Return `tx` serialized with its witness, the form every RPC takes."""
    return tx.serialize(True, check_validity=False).hex()


def _txid(tx: Tx) -> str:
    """Return `tx`'s own txid, as the node's RPC spells one."""
    return tx.id.hex()


def _fee(coins: Sequence[Utxo], tx: Tx) -> int:
    """Return what `tx`, spending `coins`, pays in fee, in satoshis."""
    return sum(coin.value for coin in coins) - sum(out.value for out in tx.vout)


def _submit(
    node: NodeAdapter, package: Sequence[Tx], *, maxfeerate: int | None = None
) -> dict[str, Any]:
    """Return `submitpackage`'s own answer for `package`.

    :param maxfeerate: `submitpackage`'s own second argument where given,
        `0` turning its fee-rate ceiling off.
    """
    params: list[object] = [[_hex(tx) for tx in package]]
    if maxfeerate is not None:
        params.append(maxfeerate)
    result = node.rpc.call("submitpackage", params)
    assert isinstance(result, dict), result
    return result


def _assert_mempool_contents(node: NodeAdapter, expected: Sequence[Tx]) -> None:
    """Assert `node`'s mempool holds `expected` and nothing else.

    Core's own `assert_mempool_contents`
    (`test/functional/test_framework/mempool_util.py`), which Core's file
    calls with `sync=False`: no transaction is listed twice, and the
    mempool is as long as `expected` and holds each of it.
    """
    txids = [_txid(tx) for tx in expected]
    assert len(txids) == len(set(txids)), txids
    mempool = node.rpc.call("getrawmempool")
    assert isinstance(mempool, list), mempool
    assert len(mempool) == len(txids), (mempool, txids)
    for txid in txids:
        assert txid in mempool, (txid, mempool)


class _Packages:
    """Core's own `create_simple_package`, and the counter it keeps.

    Core's `self.ctr` moves every sequence one below the last, so that two
    transactions spending the same coin at the same fee still differ.

    :param wallet: the wallet whose coins every package spends.
    """

    def __init__(self, wallet: MiniWallet) -> None:
        self.wallet = wallet
        self._ctr = 0

    def sequence(self) -> int:
        """Return the next of Core's `MAX_BIP125_RBF_SEQUENCE - self.ctr`."""
        self._ctr += 1
        return _MAX_BIP125_RBF_SEQUENCE - self._ctr

    def simple(
        self,
        parent_coin: Utxo,
        parent_fee: int = _DEFAULT_FEE,
        child_fee: int = _DEFAULT_CHILD_FEE,
        *,
        heavy_child: bool = False,
    ) -> list[Tx]:
        """Return a parent spending `parent_coin` and a child spending it.

        :param parent_coin: the coin the parent spends.
        :param parent_fee: the parent's own fee, in satoshis.
        :param child_fee: the child's own fee, in satoshis, spread over
            its outputs as Core's `fee_per_output` spreads it.
        :param heavy_child: give the child `_HEAVY_CHILD_OUTPUTS` outputs
            rather than one.
        """
        sequence = self.sequence()
        parent = self.wallet.create_self_transfer(
            fee=parent_fee, utxo_to_spend=parent_coin, sequence=sequence
        )
        num_outputs = _HEAVY_CHILD_OUTPUTS if heavy_child else 1
        child = self.wallet.create_self_transfer_multi(
            utxos_to_spend=[self.wallet.new_utxos(parent)[0]],
            num_outputs=num_outputs,
            fee_per_output=child_fee // num_outputs,
            sequence=sequence,
        )
        return [parent, child]


def _node(
    cluster: _Cluster, skip_counts: SkipCounts, *capabilities: Capability, coins: int
) -> tuple[NodeAdapter, _Packages]:
    """Return a fresh node and a wallet holding `coins` matured coinbases.

    :param capabilities: what the body asks for besides
        `Capability.PACKAGE_ACCEPTANCE`, asked for first, and
        `Capability.MINE`, asked for last.
    :param coins: how many coinbases have matured once the wallet mines.
    """
    (node,) = cluster(1)
    for capability in (Capability.PACKAGE_ACCEPTANCE, *capabilities, Capability.MINE):
        require(capability, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + coins)
    return node, _Packages(wallet)


def a_child_pays_to_replace_its_parents_conflicts(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a package replaces its parent's conflicts, on the node and a peer.

    Core's `test_package_rbf_basic`: `testmempoolaccept` refuses the
    replacing package, conflicts being out of its reach, and
    `submitpackage` takes it, naming what it replaced; the peer follows
    the replacement over p2p.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    nodes = cluster(2)
    node, peer = nodes
    for capability in (
        Capability.PACKAGE_ACCEPTANCE,
        Capability.CONNECT,
        Capability.MINE,
    ):
        require(capability, node.capabilities, skip_counts)
    connect_nodes(peer, node)
    packages = _Packages(MiniWallet(node))
    packages.wallet.generate(COINBASE_MATURITY + 1)
    sync_all(nodes)

    parent_coin = packages.wallet.get_utxo()
    package1 = packages.simple(parent_coin, _DEFAULT_FEE, _DEFAULT_FEE)
    package2 = packages.simple(parent_coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE)
    _submit(node, package1)
    _assert_mempool_contents(node, package1)
    sync_all(nodes)

    testres = node.rpc.call("testmempoolaccept", [[_hex(tx) for tx in package2]])
    assert testres[0]["reject-reason"] == "bip125-replacement-disallowed", testres

    submitres = _submit(node, package2)
    assert set(submitres["replaced-transactions"]) == {_txid(tx) for tx in package1}
    _assert_mempool_contents(node, package2)
    sync_all(nodes)


def a_child_pays_to_replace_a_single_conflict(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a child pays for its parent to replace one lone transaction.

    Core's `test_package_rbf_singleton`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=1)
    singleton_coin = packages.wallet.get_utxo()
    singleton_tx = packages.wallet.create_self_transfer(utxo_to_spend=singleton_coin)
    node.rpc.call("sendrawtransaction", [_hex(singleton_tx)])
    _assert_mempool_contents(node, [singleton_tx])

    package = packages.simple(
        singleton_coin, _DEFAULT_FEE, _fee([singleton_coin], singleton_tx) * 2
    )
    submitres = _submit(node, package)
    assert submitres["replaced-transactions"] == [_txid(singleton_tx)], submitres
    _assert_mempool_contents(node, package)


def a_package_must_pay_more_and_for_its_own_relay(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a package replacement's absolute fee, and its CPFP structure.

    Core's `test_package_rbf_additional_fees`: a replacement paying less
    than it replaces is refused though its fee rate is higher, one paying
    more by less than the incremental relay fee of its own size is
    refused, and one paying that is taken; then a replacement whose
    parent pays at least the package's own fee rate is refused, and one
    whose child pays one satoshi more is taken.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=2)
    coin = packages.wallet.get_utxo()

    package1 = packages.simple(coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE, heavy_child=True)
    assert package1[-1].vsize <= _HEAVY_CHILD_MAX_VSIZE, package1[-1].vsize
    _submit(node, package1)
    _assert_mempool_contents(node, package1)

    package_fee = _DEFAULT_FEE + _DEFAULT_CHILD_FEE
    package2 = packages.simple(coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE - 1)
    pkg_results2 = _submit(node, package2)
    assert pkg_results2["package_msg"] == (
        "package RBF failed: insufficient anti-DoS fees, rejecting replacement "
        f"{_txid(package2[1])}, less fees than conflicting txs; "
        f"{btc_from_sats(package_fee - 1)} < {btc_from_sats(package_fee)}"
    ), pkg_results2
    _assert_mempool_contents(node, package1)

    package_3_size = sum(tx.vsize for tx in packages.simple(coin))
    incremental_sats_required = int(
        Decimal(package_3_size * _INCREMENTAL_RELAY_FEE).quantize(Decimal(1))
    )
    incremental_sats_short = incremental_sats_required - 5
    failure_package3 = packages.simple(
        coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE + incremental_sats_short
    )
    assert sum(tx.vsize for tx in failure_package3) == package_3_size
    pkg_results3 = _submit(node, failure_package3)
    assert pkg_results3["package_msg"] == (
        "package RBF failed: insufficient anti-DoS fees, rejecting replacement "
        f"{_txid(failure_package3[1])}, not enough additional fees to relay; "
        f"{btc_from_sats(incremental_sats_short):.8f} < "
        f"{btc_from_sats(incremental_sats_required):.8f}"
    ), pkg_results3
    _assert_mempool_contents(node, package1)

    success_package3 = packages.simple(
        coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE + incremental_sats_required
    )
    _submit(node, success_package3)
    _assert_mempool_contents(node, success_package3)
    packages.wallet.generate(1, confirm=success_package3)

    coin = packages.wallet.get_utxo()
    package4 = packages.simple(coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE)
    _submit(node, package4)
    _assert_mempool_contents(node, package4)
    package5 = packages.simple(coin, _DEFAULT_CHILD_FEE, _DEFAULT_CHILD_FEE)
    pkg_results5 = _submit(node, package5)
    assert (
        "package RBF failed: package feerate is less than or equal to parent feerate"
        in pkg_results5["package_msg"]
    ), pkg_results5
    _assert_mempool_contents(node, package4)

    package5_1 = packages.simple(coin, _DEFAULT_CHILD_FEE, _DEFAULT_CHILD_FEE + 1)
    _submit(node, package5_1)
    _assert_mempool_contents(node, package5_1)


def a_package_replaces_no_more_clusters_than_the_limit(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a package conflicting with too many clusters is refused.

    Core's `test_package_rbf_max_conflicts`: a parent double-spending the
    first transaction of one more chain than `_MAX_REPLACEMENT_CANDIDATES`
    is refused, and so is one reaching that many chains and a lone
    transaction besides; one reaching exactly that many chains is taken.

    A build before the cluster mempool counts the transactions replaced
    instead, as Core's file of that build does: its chains are two
    transactions long, one more than half the limit of them are replaced
    by the first package, and the refusal is the package's own message,
    naming the child.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    # the cluster mempool's own count is the larger one, so the coins it
    # needs are mined whichever build this is
    node, packages = _node(cluster, skip_counts, coins=_MAX_REPLACEMENT_CANDIDATES + 2)
    clustered = Capability.CLUSTER_LINEARIZATION in node.capabilities
    chain_length = 3 if clustered else 2
    num_coins = (
        _MAX_REPLACEMENT_CANDIDATES + 1
        if clustered
        else _MAX_REPLACEMENT_CANDIDATES // chain_length + 1
    )
    wallet = packages.wallet
    parent_coins = [wallet.get_utxo() for _ in range(num_coins)]

    chains = [
        wallet.send_self_transfer_chain(chain_length=chain_length, utxo_to_spend=coin)
        for coin in parent_coins
    ]
    expected_txns = [tx for chain in chains for tx in chain]
    assert len(expected_txns) == num_coins * chain_length
    _assert_mempool_contents(node, expected_txns)

    def package_over(coins: list[Utxo]) -> list[Tx]:
        parent = wallet.create_self_transfer_multi(
            utxos_to_spend=coins, fee_per_output=_PARENT_FEE_PER_CONFLICT
        )
        child = wallet.create_self_transfer(
            fee_rate=_CHILD_FEE_RATE, utxo_to_spend=wallet.new_utxos(parent)[0]
        )
        return [parent, child]

    def assert_refused(package: list[Tx], replaced: int) -> None:
        """Assert `package` is refused for reaching `replaced` conflicts."""
        pkg_results = _submit(node, package, maxfeerate=0)
        if clustered:
            assert pkg_results["package_msg"] == "transaction failed", pkg_results
            tx_result = pkg_results["tx-results"][package[0].hash.hex()]
            assert tx_result["error"] == (
                f"too many potential replacements, rejecting replacement "
                f"{_txid(package[0])}; too many conflicting clusters "
                f"({num_coins} > {_MAX_REPLACEMENT_CANDIDATES})"
            ), tx_result
        else:
            assert pkg_results["package_msg"] == (
                "package RBF failed: too many potential replacements, rejecting "
                f"replacement {_txid(package[1])}; too many potential "
                f"replacements ({replaced} > {_MAX_REPLACEMENT_CANDIDATES})"
            ), pkg_results
        _assert_mempool_contents(node, expected_txns)

    assert_refused(package_over(parent_coins), num_coins * chain_length)

    singleton_coin = wallet.get_utxo()
    singleton_tx = wallet.create_self_transfer(utxo_to_spend=singleton_coin)
    node.rpc.call("sendrawtransaction", [_hex(singleton_tx)])
    expected_txns.append(singleton_tx)

    assert_refused(
        package_over([*parent_coins[:-1], singleton_coin]),
        (num_coins - 1) * chain_length + 1,
    )

    package = package_over(parent_coins[:-1])
    pkg_results = _submit(node, package, maxfeerate=0)
    assert pkg_results["package_msg"] == "success", pkg_results
    _assert_mempool_contents(node, [singleton_tx, *chains[-1], *package])


def a_package_with_mempool_ancestors_replaces_nothing(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a package whose child has a mempool ancestor replaces nothing.

    Core's `test_too_numerous_ancestors`: a parent conflicting with a
    package in the mempool, a second parent, and a child of both; the
    second parent enters on its own, so the child has an ancestor in the
    mempool and the replacement is refused.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=2)
    wallet = packages.wallet
    coin = wallet.get_utxo()

    package1 = packages.simple(coin, _DEFAULT_FEE, _DEFAULT_CHILD_FEE)
    _submit(node, package1)
    _assert_mempool_contents(node, package1)

    parent1 = wallet.create_self_transfer(
        fee=_DEFAULT_FEE, utxo_to_spend=coin, sequence=packages.sequence()
    )
    coin2 = wallet.get_utxo()
    parent2 = wallet.create_self_transfer(
        fee=_DEFAULT_FEE, utxo_to_spend=coin2, sequence=packages.sequence()
    )
    child = wallet.create_self_transfer_multi(
        fee_per_output=_DEFAULT_CHILD_FEE,
        utxos_to_spend=[wallet.new_utxos(parent1)[0], wallet.new_utxos(parent2)[0]],
        sequence=packages.sequence(),
    )

    pkg_result = _submit(node, [parent1, parent2, child])
    assert (
        pkg_result["package_msg"]
        == "package RBF failed: new transaction cannot have mempool ancestors"
    ), pkg_result
    _assert_mempool_contents(node, [*package1, parent2])


def a_package_with_two_parents_replaces_nothing(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a replacing package of two parents and a child is refused.

    Core's `test_package_rbf_with_wrong_pkg_size`: two packages in the
    mempool, and a package whose two parents conflict with one each and
    whose child spends both.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=2)
    wallet = packages.wallet
    coin1 = wallet.get_utxo()
    coin2 = wallet.get_utxo()

    package1 = packages.simple(coin1, _DEFAULT_FEE, _DEFAULT_CHILD_FEE)
    package2 = packages.simple(coin2, _DEFAULT_FEE, _DEFAULT_CHILD_FEE)
    _submit(node, package1)
    _submit(node, package2)
    _assert_mempool_contents(node, [*package1, *package2])
    assert len(node.rpc.call("getrawmempool")) == len(package1) + len(package2)

    parent1 = wallet.create_self_transfer(
        fee=_DEFAULT_FEE, utxo_to_spend=coin1, sequence=packages.sequence()
    )
    parent2 = wallet.create_self_transfer(
        fee=_DEFAULT_FEE, utxo_to_spend=coin2, sequence=packages.sequence()
    )
    child = wallet.create_self_transfer_multi(
        fee_per_output=_DEFAULT_CHILD_FEE,
        utxos_to_spend=[wallet.new_utxos(parent1)[0], wallet.new_utxos(parent2)[0]],
        sequence=packages.sequence(),
    )

    pkg_result = _submit(node, [parent1, parent2, child])
    assert (
        pkg_result["package_msg"]
        == "package RBF failed: package must be 1-parent-1-child"
    ), pkg_result
    _assert_mempool_contents(node, [*package1, *package2])


def a_package_must_beat_its_direct_conflicts_feerate(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a package below its direct conflict's fee rate is refused.

    Core's `test_insufficient_feerate`: the replacement pays more in all
    than the package it conflicts with, and its parent pays a satoshi
    less than the parent it conflicts with, so the feerate diagram does
    not improve.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=1)
    coin = packages.wallet.get_utxo()

    package1 = packages.simple(coin, _DEFAULT_CHILD_FEE, _DEFAULT_FEE)
    _submit(node, package1)
    _assert_mempool_contents(node, package1)

    package2 = packages.simple(coin, _DEFAULT_CHILD_FEE - 1, _DEFAULT_CHILD_FEE)
    pkg_results2 = _submit(node, package2)
    assert pkg_results2["package_msg"] == (
        "package RBF failed: insufficient feerate: does not improve feerate diagram"
    ), pkg_results2
    _assert_mempool_contents(node, package1)


def a_zero_fee_truc_parent_and_its_child_replace_a_package(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a zero-fee TRUC parent and a child paying for it replace both.

    Core's `test_0fee_package_rbf`: a TRUC package paying the default fee
    rate on each transaction is replaced by one whose parent pays nothing
    and whose child pays ten times the first package's fee.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(cluster, skip_counts, coins=1)
    wallet = packages.wallet
    parent_coin = wallet.get_utxo(confirmed_only=True)

    parent1 = wallet.create_self_transfer(utxo_to_spend=parent_coin, version=3)
    parent1_utxo = wallet.new_utxos(parent1)[0]
    child1 = wallet.create_self_transfer(utxo_to_spend=parent1_utxo, version=3)
    fees_package1 = _fee([parent_coin], parent1) + _fee([parent1_utxo], child1)
    submitres1 = _submit(node, [parent1, child1])
    assert submitres1["package_msg"] == "success", submitres1
    _assert_mempool_contents(node, [parent1, child1])

    parent2 = wallet.create_self_transfer(
        utxo_to_spend=parent_coin, fee=0, fee_rate=0, version=3
    )
    child2 = wallet.create_self_transfer(
        utxo_to_spend=wallet.new_utxos(parent2)[0], fee=fees_package1 * 10, version=3
    )
    submitres2 = _submit(node, [parent2, child2])
    assert submitres2["package_msg"] == "success", submitres2
    assert set(submitres2["replaced-transactions"]) == {
        _txid(parent1),
        _txid(child1),
    }, submitres2
    _assert_mempool_contents(node, [parent2, child2])


def a_child_double_spending_its_mempool_ancestor_is_refused(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Check a child double-spending its parent's mempool parent is refused.

    Core's `test_child_conflicts_parent_mempool_ancestor`: with the
    mempool full, a parent at the minimum relay fee rate spends a
    transaction in the mempool, and its child double-spends that
    transaction's own coin; the package is refused, its parent having an
    ancestor in the mempool, and only that ancestor stays.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, packages = _node(
        cluster, skip_counts, Capability.MAXMEMPOOL, Capability.DATACARRIER, coins=1
    )
    node.restart([_MAXMEMPOOL, _DATACARRIER])
    fill_mempool(node)
    wallet = packages.wallet
    wallet.resync()
    coin = wallet.get_utxo(confirmed_only=True)

    grandparent = wallet.create_self_transfer(
        fee=_DEFAULT_FEE, utxo_to_spend=coin, sequence=packages.sequence()
    )
    node.rpc.call("sendrawtransaction", [_hex(grandparent)])
    minrelayfeerate = sats_from_btc(node.rpc.call("getnetworkinfo")["relayfee"])

    parent = wallet.create_self_transfer(
        fee_rate=minrelayfeerate,
        utxo_to_spend=wallet.new_utxos(grandparent)[0],
        sequence=packages.sequence(),
    )
    child = wallet.create_self_transfer_multi(
        fee_per_output=_DEFAULT_CHILD_FEE,
        utxos_to_spend=[wallet.new_utxos(parent)[0], coin],
        sequence=packages.sequence(),
    )

    pkg_result = _submit(node, [parent, child])
    assert (
        pkg_result["package_msg"]
        == "package RBF failed: new transaction cannot have mempool ancestors"
    ), pkg_result
    mempool_info = node.rpc.call("getrawmempool")
    assert _txid(grandparent) in mempool_info
    assert _txid(parent) not in mempool_info
    assert _txid(child) not in mempool_info
