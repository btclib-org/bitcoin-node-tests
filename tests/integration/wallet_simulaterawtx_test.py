# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_simulaterawtx`, one body over either node.

Read from Core's `test/functional/wallet_simulaterawtx.py`
(`fa5f29774872`, 2025-12-16, the same file at the pinned `v31.1`):
`simulaterawtransaction` answers, for each wallet it is asked at, how
much a list of raw transactions would change that wallet's balance --
a watch-only descriptor counting as the wallet's own, an input the
list itself creates counting as available, a transaction the wallet
funds counting its fee -- and refuses a list spending one output twice
or spending an output neither the chain nor the list holds. Every
assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.GENERATE`, the `generatetoaddress` the body mines with, of
a fresh node of the body's own on a clean chain, as Core's
`setup_clean_chain` asks. Core's harness creates `default_wallet`
before the test runs and imports its deterministic coinbase key into
it, and Core's `generate` mines to that key's address, so the blocks
`generate` mines pay a wallet the test never reads, where the ones
`generatetoaddress` mines pay `w0`. This creates the wallet of that
name itself and mines the former to an address of its own instead.
Core's `assert_approx` is `_approx` below, the same default span. Core
reaches each wallet through `get_wallet_rpc`, as this does through
`rpc.for_wallet`.

`wallet_simulaterawtx_bitcoind_test.py` and
`wallet_simulaterawtx_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from tests.integration.wallet_signmessagewithaddress_test import refused

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["simulaterawtransaction_answers_each_wallets_balance_change"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

# `src/rpc/protocol.h`: what `simulaterawtransaction` answers a list it
# cannot simulate
_RPC_INVALID_PARAMETER = -8

_SPENT_TWICE = "Transaction(s) are spending the same output more than once"
_MISSING = "One or more transaction inputs are missing or have been spent already"

# how many blocks one `generatetoaddress` call asks for: it answers only
# once every block is mined, and has to inside the RPC client's own
# timeout (`bitcoin_core_rpc`'s `DEFAULT_TIMEOUT`)
_MINE_CHUNK = 50


def _approx(
    value: object, expected: Decimal, span: Decimal = Decimal("0.00001")
) -> None:
    """Core's own `assert_approx` (`util.py`): `value` near `expected`.

    :param value: the node's own answer.
    :param expected: what Core expects of it.
    :param span: how far from `expected` it may be.
    """
    assert isinstance(value, Decimal)
    assert expected - span <= value <= expected + span


def _generate(
    node: BitcoindAdapter | BtclibNodeAdapter, count: int, address: str
) -> None:
    """Core's `generatetoaddress`, at most `_MINE_CHUNK` blocks per call.

    :param node: the node that mines.
    :param count: how many blocks it mines.
    :param address: what each block's coinbase pays.
    """
    while count > 0:
        node.rpc.call("generatetoaddress", [min(count, _MINE_CHUNK), address])
        count -= _MINE_CHUNK


def _change(wallet: BitcoinCoreRpcClient, txs: list[str]) -> object:
    """Return `simulaterawtransaction`'s own `balance_change` for `txs`."""
    return wallet.call("simulaterawtransaction", [txs])["balance_change"]


def simulaterawtransaction_answers_each_wallets_balance_change(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    def_address = node.rpc.for_wallet(_WALLET).call("getnewaddress")
    node.rpc.call("generatetoaddress", [1, def_address])  # leave IBD

    node.rpc.call("createwallet", {"wallet_name": "w0"})
    node.rpc.call("createwallet", {"wallet_name": "w1"})
    node.rpc.call("createwallet", {"wallet_name": "w2", "disable_private_keys": True})
    w0 = node.rpc.for_wallet("w0")
    w1 = node.rpc.for_wallet("w1")
    w2 = node.rpc.for_wallet("w2")

    _generate(node, COINBASE_MATURITY + 1, w0.call("getnewaddress"))
    assert w0.call("getbalance") == 50
    assert w1.call("getbalance") == 0

    address1 = w1.call("getnewaddress")
    address2 = w1.call("getnewaddress")

    # add address1 as watch-only to w2
    import_res = w2.call(
        "importdescriptors",
        [[{"desc": w1.call("getaddressinfo", [address1])["desc"], "timestamp": "now"}]],
    )
    assert import_res[0]["success"] is True

    tx1 = node.rpc.call("createrawtransaction", [[], [{address1: 5.0}]])
    tx2 = node.rpc.call("createrawtransaction", [[], [{address2: 10.0}]])

    # w0 should be unaffected, w2 should see +5 for tx1
    assert _change(w0, [tx1]) == 0
    assert _change(w2, [tx1]) == 5
    # w1 should see +5 balance for tx1
    assert _change(w1, [tx1]) == 5
    # w0 should be unaffected, w2 should see +5 for both transactions
    assert _change(w0, [tx1, tx2]) == 0
    assert _change(w2, [tx1, tx2]) == 5
    # w1 should see +15 balance for both transactions
    assert _change(w1, [tx1, tx2]) == 15

    # w0 funds the transaction: it sees the payment and the fee go
    funding = w0.call("fundrawtransaction", [tx1])
    tx1 = funding["hex"]
    tx1changepos = funding["changepos"]
    bitcoin_fee = funding["fee"]

    # w0 sees fee + 5 btc decrease, w2 sees + 5 btc
    _approx(_change(w0, [tx1]), -(Decimal(5) + bitcoin_fee))
    _approx(_change(w2, [tx1]), Decimal(5))
    # w1 sees same as before
    assert _change(w1, [tx1]) == 5

    # same inputs (tx) more than once should error
    refused(
        w0, "simulaterawtransaction", [[tx1, tx1]], _RPC_INVALID_PARAMETER, _SPENT_TWICE
    )

    tx1hex = node.rpc.call("decoderawtransaction", [tx1])["txid"]
    tx1vout = 1 - tx1changepos
    outpoint = [{"txid": tx1hex, "vout": tx1vout}]
    # tx3 spends new w1 UTXO paying to w0
    tx3 = node.rpc.call(
        "createrawtransaction", [outpoint, {w0.call("getnewaddress"): 4.9999}]
    )
    # tx4 spends new w1 UTXO paying to w1
    tx4 = node.rpc.call(
        "createrawtransaction", [outpoint, {w1.call("getnewaddress"): 4.9999}]
    )

    # on their own, both should fail due to missing input(s)
    for tx in (tx3, tx4):
        for wallet in (w0, w1):
            refused(
                wallet,
                "simulaterawtransaction",
                [[tx]],
                _RPC_INVALID_PARAMETER,
                _MISSING,
            )

    # they should succeed when including tx1:
    #   wallet  tx3                         tx4
    #   w0      -5 - bitcoin_fee + 4.9999   -5 - bitcoin_fee
    #   w1      0                           +4.9999
    _approx(_change(w0, [tx1, tx3]), -Decimal(5) - bitcoin_fee + Decimal("4.9999"))
    _approx(_change(w1, [tx1, tx3]), Decimal(0))
    _approx(_change(w0, [tx1, tx4]), -Decimal(5) - bitcoin_fee)
    _approx(_change(w1, [tx1, tx4]), Decimal("4.9999"))

    # they should fail if attempting to include both tx3 and tx4
    for wallet in (w0, w1):
        refused(
            wallet,
            "simulaterawtransaction",
            [[tx1, tx3, tx4]],
            _RPC_INVALID_PARAMETER,
            _SPENT_TWICE,
        )

    # send tx1 to avoid reusing same UTXO below
    signed = w0.call("signrawtransactionwithwallet", [tx1])["hex"]
    node.rpc.call("sendrawtransaction", [signed])
    # confirm tx to trigger error below
    node.rpc.call("generatetoaddress", [1, def_address])

    # w0 funds transaction 2: it sees the payment and the fee go, w1 the payment
    funding = w0.call("fundrawtransaction", [tx2])
    tx2 = funding["hex"]
    bitcoin_fee2 = funding["fee"]
    _approx(_change(w0, [tx2]), -(Decimal(10) + bitcoin_fee2))
    _approx(_change(w1, [tx2]), Decimal(10))
    _approx(_change(w2, [tx2]), Decimal(0))

    # w0-w2 error due to tx1 already being mined
    for wallet in (w0, w1, w2):
        refused(
            wallet,
            "simulaterawtransaction",
            [[tx1, tx2]],
            _RPC_INVALID_PARAMETER,
            _MISSING,
        )
