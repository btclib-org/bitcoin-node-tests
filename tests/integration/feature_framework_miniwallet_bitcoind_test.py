# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_framework_miniwallet`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/feature_framework_miniwallet.py`
(`fa5f29774872`, 2025-12-16) rather than ported: that file drives
`test_framework.wallet.MiniWallet` over all three of its own modes
(`ADDRESS_OP_TRUE`, `RAW_OP_TRUE`, `RAW_P2PK`), padding each self-transfer
to an exact `target_vsize` and separately exercising a second, tagged
wallet instance. This is a smaller claim than Core's own: `mini_wallet.py`
carries one mode, Core's own default `ADDRESS_OP_TRUE` (that module's own
docstring has why), and this asks only the subject `ISS 4` is about -- a
coin mined without a node wallet, cached without `scantxoutset`, and
spendable -- rather than `target_vsize` padding or a second, tagged
wallet's own namespacing, neither of which bears on how the cache is fed.

The third test asks what Core's own file never calls and several other
Core files do: `confirmed_only`
([ISS 69](https://github.com/btclib-org/bitcoin-node-tests/issues/69)),
over a cache holding a coin this wallet's own `generate` confirmed, one
a block the node mined itself confirmed (`generateblock`, naming that one
transaction), and one only the mempool holds.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import FEE, MiniWallet

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject, narrowed: mine, cache with no scan, spend."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    balance_before = wallet.get_balance()

    tx = wallet.send_self_transfer()

    mempool = bitcoind_adapter.rpc.call("getrawmempool")
    assert isinstance(mempool, list)
    assert tx.id.hex() in mempool
    assert wallet.get_balance() == balance_before - FEE


def test_mini_wallet_spends_two_coins_in_a_row(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The cache still answers after a spend, with no re-scan in between."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 2)

    first = wallet.send_self_transfer()
    second = wallet.send_self_transfer()

    mempool = bitcoind_adapter.rpc.call("getrawmempool")
    assert isinstance(mempool, list)
    assert first.id.hex() in mempool
    assert second.id.hex() in mempool
    assert first.id != second.id


def test_mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """A mix of confirmed and mempool-only coins filters as the node sees it."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    rpc = bitcoind_adapter.rpc
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 2)
    # named rather than left to `get_utxo`'s largest-first pick, which
    # takes a self-transfer's own coin over a coinbase a halving shrank
    coinbases = wallet.get_utxos(mark_as_spent=False)
    assert len(coinbases) == 3

    mined_here = wallet.send_self_transfer(utxo_to_spend=coinbases[0])
    wallet.generate(1, confirm=[mined_here])
    mined_by_node = wallet.send_self_transfer(utxo_to_spend=coinbases[1])
    rpc.call("generateblock", [wallet.script_pub_key.address, [mined_by_node.id.hex()]])
    mempool_only = wallet.send_self_transfer(utxo_to_spend=coinbases[2])
    wallet.resync()

    confirmed = {mined_here.id, mined_by_node.id}
    everything = wallet.get_utxos(include_immature_coinbase=True, mark_as_spent=False)
    kept = wallet.get_utxos(
        include_immature_coinbase=True, mark_as_spent=False, confirmed_only=True
    )
    spends = confirmed | {mempool_only.id}
    assert {u.outpoint.tx_id for u in everything if not u.coinbase} == spends
    assert {u.outpoint.tx_id for u in kept if not u.coinbase} == confirmed
    with pytest.raises(LookupError, match="confirmed"):
        wallet.get_utxo(txid=mempool_only.id.hex(), confirmed_only=True)

    # the node's own answer agrees, coin by coin
    for tx in (mined_here, mined_by_node, mempool_only):
        in_utxo_set = rpc.call("gettxout", [tx.id.hex(), 0, False]) is not None
        assert in_utxo_set == (tx.id in confirmed)
    mempool = rpc.call("getrawmempool")
    assert isinstance(mempool, list)
    assert mempool_only.id.hex() in mempool
