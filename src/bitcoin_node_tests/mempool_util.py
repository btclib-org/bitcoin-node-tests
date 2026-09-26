# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`fill_mempool`: push a node's own mempool past its size-based eviction.

Core's own `fill_mempool`
(`test/functional/test_framework/mempool_util.py`): a throwaway
`MiniWallet` sends a run of disposable self-transfers at a steadily
rising fee rate, so that a node started with a small enough
`-maxmempool` runs out of room and starts evicting its own
lowest-feerate transaction -- the precondition several of Core's own
fee-bumping and eviction tests build before their own scenario, rather
than a mechanism this module's own callers ask questions about.

A smaller claim than Core's own function: Core's `tx_sync_fun` (or, absent
one, `test_framework.sync_mempools()`) is dropped -- every RPC this
function makes targets the one node it was given, so nothing needs
propagating to a second one first, and Core's own two callers confirm
this rather than needing the parameter, `mempool_package_rbf.py` passing
an explicit no-op and `rpc_packages.py` running a single-node test where
`sync_mempools` already has nothing to do. `tx_batch_size`, always `1` at
both call sites, is dropped for the same reason: a generality neither
caller exercises. The large low-priority output each transaction carries
is `create_self_transfer`'s own `target_vsize` padding rather than
Core's own literal `gen_return_txouts` payload, a different number of
padding bytes reaching the identical role -- a transaction whose own fee
*rate*, not its absolute fee, decides where a size-based mempool ranks it.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.amount import sats_from_btc
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "fill_mempool",
]

# Core's own `num_of_batches`: how many disposable, increasing-fee
# transactions this sends before checking that eviction has happened.
_NUM_TXS = 75

# the last this many of `_NUM_TXS` are the ones whose fee actually
# triggers eviction; the mempool is read once before them and once after
_HIGH_FEE_TXS = 3

# virtual bytes each disposable transaction is padded to, `target_vsize`
# on `create_self_transfer`: the serialized size Core's own
# `gen_return_txouts` asserts for its padding outputs (67456 bytes) plus
# the 104-vbyte unpadded self-transfer,
# large enough that `_NUM_TXS` of them at `-maxmempool=5` actually reach
# that cap's own dynamic-memory-usage accounting -- measured against a
# real `bitcoind`, a smaller target here left the mempool never evicting
# at all, the per-transaction bookkeeping `-maxmempool` counts costing
# more than the raw serialized size alone
_TARGET_VSIZE = 67_560


def fill_mempool(node: NodeAdapter) -> None:
    """Fill `node`'s own mempool with disposable transactions until eviction.

    A throwaway `MiniWallet` mines its own coins, then sends one
    unpadded, minimum-fee-rate self-transfer -- the one this function
    expects back out of the mempool by the time it returns -- followed by
    `_NUM_TXS` padded self-transfers, each at `_TARGET_VSIZE` and at a
    fee a further multiple of `base_fee` (twice the node's own `relayfee`
    over `_TARGET_VSIZE`) than the one before it. The mempool is read once
    after the first `_NUM_TXS - _HIGH_FEE_TXS` of them, confirming
    eviction has not started early, and once more after the rest,
    confirming it has: `mempoolminfee` above `minrelaytxfee`, and the
    first, minimum-fee-rate transaction gone.

    :param node: the node whose own mempool this fills, started with a
        small enough `-maxmempool` (Core's own docstring names `5`,
        megabytes) that `_NUM_TXS` transactions at `_TARGET_VSIZE` each
        exhaust it.
    :raises AssertionError: eviction started before the last
        `_HIGH_FEE_TXS` transactions were sent, or never started at all --
        `mempoolminfee` still at `minrelaytxfee` afterwards, the low
        fee-rate transaction still in the mempool, or the mempool holding
        as many transactions as this function sent.
    :raises LookupError: forwarded from `MiniWallet.get_utxo` -- the
        wallet did not mine `_NUM_TXS + 1` coins to spend.
    :raises TypeError: forwarded from `MiniWallet.generate` or
        `MiniWallet.send_self_transfer` -- the node's RPC answered
        something one of those calls cannot use.
    :raises ValueError: forwarded from `MiniWallet.send_self_transfer`.
    """
    wallet = MiniWallet(node)
    wallet.generate(_NUM_TXS + 1)
    # enough further blocks that every coin mined above clears
    # `COINBASE_MATURITY`, Core's own reason for this second `generate`
    wallet.generate(COINBASE_MATURITY - 1)

    relay_fee = node.rpc.call("getnetworkinfo")["relayfee"]
    relay_fee_rate = sats_from_btc(relay_fee)
    # Core's own `base_fee`: twice `relay_fee_rate` over `_TARGET_VSIZE`,
    # each of the `_NUM_TXS` transactions a further multiple of it
    base_fee = relay_fee_rate * 2 * (_TARGET_VSIZE // 1000)
    batch_fees = [(index + 1) * base_fee for index in range(_NUM_TXS)]

    confirmed_utxos = [
        wallet.get_utxo(confirmed_only=True) for _ in range(_NUM_TXS + 1)
    ]
    evicted = wallet.send_self_transfer(
        utxo_to_spend=confirmed_utxos.pop(0), fee_rate=relay_fee_rate
    )

    for fee in batch_fees[:-_HIGH_FEE_TXS]:
        wallet.send_self_transfer(
            utxo_to_spend=confirmed_utxos.pop(0), fee=fee, target_vsize=_TARGET_VSIZE
        )
    mempool_info = node.rpc.call("getmempoolinfo")
    if mempool_info["mempoolminfee"] != relay_fee:
        err_msg = (
            f"mempoolminfee {mempool_info['mempoolminfee']} already above "
            f"relayfee {relay_fee} before the last {_HIGH_FEE_TXS} "
            "transactions were sent"
        )
        raise AssertionError(err_msg)

    for fee in batch_fees[-_HIGH_FEE_TXS:]:
        wallet.send_self_transfer(
            utxo_to_spend=confirmed_utxos.pop(0), fee=fee, target_vsize=_TARGET_VSIZE
        )

    mempool = node.rpc.call("getrawmempool")
    if len(mempool) >= _NUM_TXS:
        err_msg = f"{len(mempool)} transactions still in the mempool, none evicted"
        raise AssertionError(err_msg)
    if evicted.id.hex() in mempool:
        err_msg = f"the minimum fee-rate transaction {evicted.id.hex()} was not evicted"
        raise AssertionError(err_msg)

    mempool_info = node.rpc.call("getmempoolinfo")
    if mempool_info["minrelaytxfee"] != relay_fee:
        err_msg = f"minrelaytxfee {mempool_info['minrelaytxfee']} moved off {relay_fee}"
        raise AssertionError(err_msg)
    if mempool_info["mempoolminfee"] <= relay_fee:
        err_msg = f"mempoolminfee {mempool_info['mempoolminfee']} did not rise above {relay_fee}"
        raise AssertionError(err_msg)
