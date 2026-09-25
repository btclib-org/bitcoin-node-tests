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
