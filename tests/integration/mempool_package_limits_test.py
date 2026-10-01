# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_package_limits`, one body per test over either node.

Read from Core's `test/functional/mempool_package_limits.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the option and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-limitclustercount` (`Capability.LIMIT_CLUSTER_COUNT`) caps how many
transactions one mempool cluster may hold, in-mempool and in-package
together, and `MiniWallet.send_self_transfer_chain` /
`create_self_transfer_multi` build the two shapes Core's own file checks
that boundary with, each package handed to `testmempoolaccept` to
evaluate as one (`Capability.PACKAGE_ACCEPTANCE`).

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

Each body starts its node without `-limitclustercount` and, where the
node declares the capability, restarts it with the option before any
block is mined. A build before the cluster mempool (`v31.0`) has no such
option: it limits the same shapes at its defaults of 25 in-mempool
ancestors and 25 descendants, and refuses a package over them with
`package-mempool-limits`, so the body runs there at those defaults and
matches that reason.

`mempool_package_limits_bitcoind_test.py` and
`mempool_package_limits_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "in_package_ancestors_count_toward_the_mempool_ancestor_limit",
    "in_package_descendants_count_toward_the_mempool_descendant_limit",
]

_LIMIT_CLUSTER_COUNT = 25


def _package_hex(txs: list[Tx]) -> list[str]:
    return [tx.serialize(True, check_validity=False).hex() for tx in txs]


def _assert_all_refused(
    node: NodeAdapter, package: list[Tx], *, clustered: bool
) -> None:
    refusal = "too-large-cluster" if clustered else "package-mempool-limits"
    results = node.rpc.call("testmempoolaccept", [_package_hex(package)])
    assert isinstance(results, list)
    assert len(results) == len(package)
    for result in results:
        assert refusal in result["package-error"], result


def _assert_all_allowed(node: NodeAdapter, package: list[Tx]) -> None:
    results = node.rpc.call("testmempoolaccept", [_package_hex(package)])
    assert isinstance(results, list)
    assert all(result["allowed"] for result in results), results


def _start(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> tuple[BitcoindAdapter | BtclibNodeAdapter, bool]:
    """Return one node and whether it runs the cluster mempool.

    A node declaring `Capability.LIMIT_CLUSTER_COUNT` is restarted with
    `-limitclustercount`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PACKAGE_ACCEPTANCE, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    clustered = Capability.LIMIT_CLUSTER_COUNT in node.capabilities
    if clustered:
        node.restart([f"-limitclustercount={_LIMIT_CLUSTER_COUNT}"])
    return node, clustered


def in_package_ancestors_count_toward_the_mempool_ancestor_limit(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check 24 in-mempool ancestors and a 2-tx package exceed the limit of 25.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, clustered = _start(cluster, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    assert node.rpc.call("getmempoolinfo")["size"] == 0

    chain = wallet.send_self_transfer_chain(chain_length=24)
    assert node.rpc.call("getmempoolinfo")["size"] == 24
    chain_tip = wallet.get_utxo(txid=chain[-1].id.hex(), vout=0)
    parent = wallet.create_self_transfer(utxo_to_spend=chain_tip)
    parent_utxo = wallet.new_utxos(parent)[0]
    child = wallet.create_self_transfer(utxo_to_spend=parent_utxo)
    package = [parent, child]

    _assert_all_refused(node, package, clustered=clustered)

    node.mine(1)
    assert node.rpc.call("getmempoolinfo")["size"] == 0
    _assert_all_allowed(node, package)


def in_package_descendants_count_toward_the_mempool_descendant_limit(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a top parent's own descendants exceed the limit counted together.

    A top parent with two chains hanging off it, 11 and 12 transactions
    deep -- 24 in-mempool descendants including the parent itself -- and
    a package extending each chain by one more transaction: the top
    parent's own descendant count only exceeds 25 once the package's two
    transactions join the 24 already in the mempool.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node, clustered = _start(cluster, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)

    top_parent = wallet.send_self_transfer_multi(num_outputs=2)
    first_leg = wallet.get_utxo(txid=top_parent.id.hex(), vout=0)
    second_leg = wallet.get_utxo(txid=top_parent.id.hex(), vout=1)
    chain_a = wallet.send_self_transfer_chain(chain_length=11, utxo_to_spend=first_leg)
    chain_b = wallet.send_self_transfer_chain(chain_length=12, utxo_to_spend=second_leg)
    assert node.rpc.call("getmempoolinfo")["size"] == 1 + 11 + 12

    chain_a_tip = wallet.get_utxo(txid=chain_a[-1].id.hex(), vout=0)
    chain_b_tip = wallet.get_utxo(txid=chain_b[-1].id.hex(), vout=0)
    package = [
        wallet.create_self_transfer(utxo_to_spend=chain_a_tip),
        wallet.create_self_transfer(utxo_to_spend=chain_b_tip),
    ]

    _assert_all_refused(node, package, clustered=clustered)

    node.mine(1)
    assert node.rpc.call("getmempoolinfo")["size"] == 0
    _assert_all_allowed(node, package)
