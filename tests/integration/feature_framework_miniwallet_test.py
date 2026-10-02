# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_framework_miniwallet`, one body per test over either node.

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

The third body asks what Core's own file never calls and several other
Core files do: `confirmed_only`
([ISS 69](https://github.com/btclib-org/bitcoin-node-tests/issues/69)),
over a cache holding a coin this wallet's own `generate` confirmed, one
a block the node mined itself confirmed (`generateblock`, naming that one
transaction), and one only the mempool holds.

The last two ask what Core's own `mempool_truc.py` and
`mempool_package_rbf.py` rest on
([ISS 103](https://github.com/btclib-org/bitcoin-node-tests/issues/103)):
that a caller-chosen `fee_rate` is the fee `getmempoolentry` reports,
priced over the tx's own vsize or over `target_vsize`, and not refused
above `sendrawtransaction`'s own default `maxfeerate`; and that
`version=3` is a transaction the node holds to TRUC's own policy -- one
over `TRUC_MAX_VSIZE` (`src/policy/truc_policy.h`) refused where the
same size at version 2 is accepted.

Each of those two restarts the session's node with a `-datacarriersize`
(`Capability.DATACARRIER`) over its `target_vsize` padding, and without
it once done: `v29.4` refuses that padding by default with `scriptpubkey`
(bitcoin/bitcoin#32406, first in `v30.0rc1`).

`feature_framework_miniwallet_bitcoind_test.py` and
`feature_framework_miniwallet_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import (
    DEFAULT_FEE_RATE,
    PADDING_DATACARRIER_SIZE,
    MiniWallet,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones",
    "mini_wallet_fee_rate_is_the_fee_the_node_reports",
    "mini_wallet_spends_a_coin_it_mined_without_a_node_wallet",
    "mini_wallet_spends_two_coins_in_a_row",
    "mini_wallet_version_3_is_held_to_truc_policy",
]

# `src/policy/truc_policy.h`'s own `TRUC_MAX_VSIZE`, virtual bytes
_TRUC_MAX_VSIZE = 10_000


@contextmanager
def _padding_allowed(adapter: BitcoindAdapter | BtclibNodeAdapter) -> Iterator[None]:
    """Run with a `-datacarriersize` over `target_vsize`'s padding.

    The session's node is shared, so it restarts without the option after.
    """
    adapter.restart([f"-datacarriersize={PADDING_DATACARRIER_SIZE}"])
    try:
        yield
    finally:
        adapter.restart()


def _base_fee(entry: object) -> int:
    """Return a `getmempoolentry` answer's own `fees.base`, in satoshis."""
    assert isinstance(entry, dict)
    return int(Decimal(str(entry["fees"]["base"])) * 100_000_000)


def mini_wallet_spends_a_coin_it_mined_without_a_node_wallet(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject, narrowed: mine, cache with no scan, spend.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.MINE, adapter.capabilities, skip_counts)
    wallet = MiniWallet(adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    balance_before = wallet.get_balance()

    tx = wallet.send_self_transfer()

    mempool = adapter.rpc.call("getrawmempool")
    assert isinstance(mempool, list)
    assert tx.id.hex() in mempool
    fee = -(-DEFAULT_FEE_RATE * tx.vsize // 1000)
    assert wallet.get_balance() == balance_before - fee


def mini_wallet_spends_two_coins_in_a_row(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Spend twice from the cache, with no re-scan in between.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.MINE, adapter.capabilities, skip_counts)
    wallet = MiniWallet(adapter)
    wallet.generate(COINBASE_MATURITY + 2)

    first = wallet.send_self_transfer()
    second = wallet.send_self_transfer()

    mempool = adapter.rpc.call("getrawmempool")
    assert isinstance(mempool, list)
    assert first.id.hex() in mempool
    assert second.id.hex() in mempool
    assert first.id != second.id


def mini_wallet_confirmed_only_tells_mined_coins_from_mempool_ones(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Filter a mix of confirmed and mempool-only coins as the node sees it.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.GENERATE, adapter.capabilities, skip_counts)
    require(Capability.MINE, adapter.capabilities, skip_counts)
    rpc = adapter.rpc
    wallet = MiniWallet(adapter)
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


def mini_wallet_fee_rate_is_the_fee_the_node_reports(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """`fee_rate` over the vsize, or `target_vsize`, is `fees.base`.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.MINE, adapter.capabilities, skip_counts)
    require(Capability.DATACARRIER, adapter.capabilities, skip_counts)
    with _padding_allowed(adapter):
        rpc = adapter.rpc
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 3)

        unpadded = wallet.send_self_transfer(fee_rate=12_345)
        padded = wallet.send_self_transfer(fee_rate=12_345, target_vsize=250)
        # 0.2 BTC/kvB, twice the default `maxfeerate` a bare call is held to
        above_ceiling = wallet.send_self_transfer(fee_rate=20_000_000)

        unpadded_entry = rpc.call("getmempoolentry", [unpadded.id.hex()])
        assert unpadded_entry["vsize"] == unpadded.vsize
        # 12_345 sat/kvB over 104 vB is 1283.88 sat, rounded up
        assert _base_fee(unpadded_entry) == 1284
        padded_entry = rpc.call("getmempoolentry", [padded.id.hex()])
        assert padded_entry["vsize"] == 250
        # over 250 vB, 3086.25 sat, rounded up
        assert _base_fee(padded_entry) == 3087
        above_ceiling_entry = rpc.call("getmempoolentry", [above_ceiling.id.hex()])
        assert _base_fee(above_ceiling_entry) == 2_080_000


def mini_wallet_version_3_is_held_to_truc_policy(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Send a `version=3` tx, accepted, and one past TRUC's own size cap.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.MINE, adapter.capabilities, skip_counts)
    require(Capability.DATACARRIER, adapter.capabilities, skip_counts)
    with _padding_allowed(adapter):
        rpc = adapter.rpc
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 3)

        truc = wallet.send_self_transfer(version=3)
        assert (
            rpc.call("decoderawtransaction", [truc.serialize(True).hex()])["version"]
            == 3
        )
        mempool = rpc.call("getrawmempool")
        assert isinstance(mempool, list)
        assert truc.id.hex() in mempool

        oversize = _TRUC_MAX_VSIZE + 1
        wallet.send_self_transfer(version=2, target_vsize=oversize)
        too_big = wallet.create_self_transfer(version=3, target_vsize=oversize)
        with pytest.raises(
            RpcError, match="TRUC-violation, version=3 tx .* is too big"
        ):
            rpc.call("sendrawtransaction", [too_big.serialize(True).hex()])
