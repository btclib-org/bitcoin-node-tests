# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_expiry`, one body over either node.

Read from Core's `test/functional/mempool_expiry.py` (`fa5f29774872`,
2025-12-16), the option, MiniWallet and clock families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a transaction still in the mempool five seconds short of the expiry
timeout is gone five seconds past it, the child spending it goes with
it, an independent transaction stays, and a prioritisation given to the
expired transaction outlives it. The timeout is Core's own default,
`DEFAULT_MEMPOOL_EXPIRY_HOURS` (`src/kernel/mempool_options.h`), and
then Core's own custom value, the node restarted with `-mempoolexpiry`
(`Capability.MEMPOOL_EXPIRY`), one after the other over one node as
Core's own `run_test` runs them. The hours pass on the node's own clock
(`Capability.CLOCK`), and each check follows a transaction sent to the
mempool, which Core's own file notes is the only moment expiry is
checked. `MiniWallet` (`Capability.MINE`) funds every transaction.

Core's own claim in full. Its chain is the framework's cached one; this
node mines its own, deep enough to mature the coins both passes spend.
Core reads the parent's fee off `send_self_transfer`'s answer; this
reads it off the coin spent and the output paid, `MiniWallet` returning
the transaction rather than Core's dictionary.

`mempool_expiry_bitcoind_test.py` and `mempool_expiry_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["a_transaction_and_its_child_expire_together"]

# Core's own `COIN`, `DEFAULT_MEMPOOL_EXPIRY_HOURS` and
# `CUSTOM_MEMPOOL_EXPIRY`
_COIN = 100_000_000
_DEFAULT_MEMPOOL_EXPIRY_HOURS = 336
_CUSTOM_MEMPOOL_EXPIRY = 10

# `RPC_INVALID_ADDRESS_OR_KEY` (`src/rpc/protocol.h`), and Core's own
# wording for a transaction `getmempoolentry` does not find
_NOT_IN_MEMPOOL_CODE = -5
_NOT_IN_MEMPOOL = "Transaction not in mempool"

# the coins both passes spend, matured: each spends a parent, an
# independent coin and two triggers
_MATURE_COINS = 8


def _assert_not_in_mempool(node: NodeAdapter, txid: str) -> None:
    """Core's `assert_raises_rpc_error(-5, ..., node.getmempoolentry, txid)`."""
    with pytest.raises(RpcError) as refused:
        node.rpc.call("getmempoolentry", [txid])
    assert refused.value.code == _NOT_IN_MEMPOOL_CODE
    assert _NOT_IN_MEMPOOL in str(refused.value)


def _entry(node: NodeAdapter, txid: str) -> dict[str, object]:
    """Return `getmempoolentry`'s own answer for `txid`."""
    entry = node.rpc.call("getmempoolentry", [txid])
    assert isinstance(entry, dict)
    return entry


def _test_transaction_expiry(
    node: NodeAdapter, wallet: MiniWallet, timeout: int
) -> None:
    """Core's own `test_transaction_expiry`, over `timeout` hours.

    :param node: the node under test.
    :param wallet: funding every transaction sent.
    :param timeout: the expiry the node was started with, in hours.
    """
    # a parent transaction that will expire
    spent = wallet.get_utxo(mark_as_spent=False)
    parent = wallet.send_self_transfer(utxo_to_spend=spent)
    parent_txid = parent.id.hex()
    parent_fee = spent.value - parent.vout[0].value
    parent_utxo = wallet.get_utxo(txid=parent_txid)
    independent_utxo = wallet.get_utxo()

    # a prioritisation that persists after the expiry
    node.rpc.call("prioritisetransaction", [parent_txid, 0, _COIN])
    prioritised = node.rpc.call("getprioritisedtransactions")
    assert isinstance(prioritised, dict)
    assert prioritised[parent_txid] == {
        "fee_delta": _COIN,
        "in_mempool": True,
        "modified_fee": _COIN + parent_fee,
    }

    # coins independent of the transactions whose expiry is checked
    trigger_utxo1 = wallet.get_utxo()
    trigger_utxo2 = wallet.get_utxo()

    entry_time = _entry(node, parent_txid)["time"]
    assert isinstance(entry_time, int)
    node.set_mock_time(entry_time)

    # half the timeout on, a child spending the parent
    half_expiry_time = entry_time + int(60 * 60 * timeout / 2)
    node.set_mock_time(half_expiry_time)
    child_txid = wallet.send_self_transfer(utxo_to_spend=parent_utxo).id.hex()
    depends = _entry(node, child_txid)["depends"]
    assert isinstance(depends, list)
    assert parent_txid == depends[0]

    # and an independent transaction
    independent_txid = wallet.send_self_transfer(
        utxo_to_spend=independent_utxo
    ).id.hex()

    # nearly the whole timeout on, the parent is still there: expiry runs
    # only when a transaction joins the mempool, so one is sent
    nearly_expiry_time = entry_time + 60 * 60 * timeout - 5
    node.set_mock_time(nearly_expiry_time)
    wallet.send_self_transfer(utxo_to_spend=trigger_utxo1)
    assert entry_time == _entry(node, parent_txid)["time"]

    # past the timeout, it is gone
    expiry_time = entry_time + 60 * 60 * timeout + 5
    node.set_mock_time(expiry_time)
    wallet.send_self_transfer(utxo_to_spend=trigger_utxo2)
    _assert_not_in_mempool(node, parent_txid)

    # its prioritisation is not
    prioritised = node.rpc.call("getprioritisedtransactions")
    assert isinstance(prioritised, dict)
    assert prioritised[parent_txid] == {"fee_delta": _COIN, "in_mempool": False}

    # its child is gone too, and the independent transaction stays
    _assert_not_in_mempool(node, child_txid)
    assert half_expiry_time == _entry(node, independent_txid)["time"]


def a_transaction_and_its_child_expire_together(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check both expiries Core's own `run_test` checks, default then custom.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MEMPOOL_EXPIRY, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + _MATURE_COINS)

    _test_transaction_expiry(node, wallet, _DEFAULT_MEMPOOL_EXPIRY_HOURS)

    node.restart([f"-mempoolexpiry={_CUSTOM_MEMPOOL_EXPIRY}"])
    _test_transaction_expiry(node, wallet, _CUSTOM_MEMPOOL_EXPIRY)
