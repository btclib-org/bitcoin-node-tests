# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_utxo_set_hash`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_utxo_set_hash.py`
(`58eeab790d98`, 2026-05-13) and narrowed to what the MiniWallet family
reaches
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`MiniWallet.generate`/`send_self_transfer` (`Capability.MINE`) build a
short chain, and `btclib.coinstats.CoinStats` -- covered in
`TF2.md`'s own entry for `test_framework/crypto/muhash.py` -- is what
computes the UTXO set's own MuHash commitment independently of the node
under test, walking every block the node itself hands back over
`getblock` rather than trusting Core's own Python reimplementation the
way Core's own file does.

Not the clock family, unlike Core's own file: Core's own `setmocktime`
call there freezes the clock its own node-driven mining
(`generatetodescriptor`) reads block times from -- this harness's own
`MiniWallet.generate` (`mini_wallet.py`'s own docstring) always builds a
block's own time from the wall clock instead, client-side, so freezing
the node's clock only produces a `time-too-new` refusal once real time
has moved past whatever the freeze holds it at, proven live: setting it
to the tip's own time, as Core's file does, fails the very first block
this harness tries to submit afterwards.

A smaller claim than Core's own file: kept is that both of this
repository's own independently computed commitments agree with
`gettxoutsetinfo`'s own -- `muhash`, and `hash_serialized_3`, the SHA256d
Core's `kernel/coinstats.cpp` takes over the same `TxOutSer` bytes MuHash
is fed, in the order its coins-view cursor walks them (by txid as stored,
then by output index) -- across a chain carrying a coinbase-only run and
one spend. Dropped is Core's own two hard-coded `hash_serialized_3` and
`muhash` literals: deterministic only on Core's own exact chain (its own
node-wallet addresses, its own mining order), which this harness's own
MiniWallet-mined chain has no reason to reproduce.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.block.block import Block
from btclib.coinstats import CoinStats, tx_out_ser
from btclib.hashes import hash256
from btclib.script import is_unspendable
from btclib.tx import OutPoint
from btclib.tx.coin import Coin
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def _independent_utxo_set(
    adapter: BitcoindAdapter, tip_height: int
) -> dict[bytes, Coin]:
    """Walk every block but the genesis, and return the UTXO set they leave.

    Keyed by serialized outpoint; an unspendable output is left out, as
    Core never writes one to its coins view.

    The genesis block's own coinbase is never inserted: `btclib.coinstats`'s
    own module docstring has why -- "spendable-looking and unspendable",
    a fact about this chain rather than about any output's own script,
    and so the caller's to apply rather than `CoinStats.insert`'s.

    :param adapter: the node to read every block back from.
    :param tip_height: the last height to walk, inclusive.
    """
    spent: set[bytes] = set()
    coins: dict[bytes, Coin] = {}
    for height in range(1, tip_height + 1):
        block_hash = adapter.rpc.call("getblockhash", [height])
        block_hex = adapter.rpc.call("getblock", [block_hash, 0])
        block = Block.parse(bytes.fromhex(block_hex), check_validity=False)
        for tx_index, tx in enumerate(block.transactions):
            is_coinbase = tx_index == 0
            if not is_coinbase:
                spent.update(tx_in.prev_out.serialize() for tx_in in tx.vin)
            for vout_index, tx_out in enumerate(tx.vout):
                key = OutPoint(tx.id, vout_index).serialize()
                coins[key] = Coin(tx_out, height, is_coinbase, check_validity=False)
    return {
        key: coin
        for key, coin in coins.items()
        if key not in spent and not is_unspendable(coin.tx_out.script_pub_key.script)
    }


def _hash_serialized_3(utxo_set: dict[bytes, Coin]) -> bytes:
    """Return Core's `hash_serialized_3` over `utxo_set`, in its own byte order.

    SHA256d over every coin's `TxOutSer`, in the order Core's coins-view
    cursor walks them: by the txid's own stored bytes, then by output
    index (`ApplyHash`'s `std::map<uint32_t, Coin>`).
    """
    ordered = sorted(
        utxo_set.items(),
        key=lambda item: (item[0][:32], int.from_bytes(item[0][32:], "little")),
    )
    return hash256(b"".join(tx_out_ser(key, coin) for key, coin in ordered))


def test_independent_muhash_matches_gettxoutsetinfo(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """`CoinStats`, walked off the node's own blocks, agrees with the node."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    tx = wallet.create_self_transfer()
    bitcoind_adapter.rpc.call(
        "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
    )
    wallet.generate(1, confirm=[tx])

    tip_height = bitcoind_adapter.rpc.call("getblockcount")
    utxo_set = _independent_utxo_set(bitcoind_adapter, tip_height)
    stats = CoinStats()
    for key, coin in utxo_set.items():
        stats.insert(key, coin)
    node_muhash = bitcoind_adapter.rpc.call("gettxoutsetinfo", ["muhash"])["muhash"]
    node_hash_serialized_3 = bitcoind_adapter.rpc.call("gettxoutsetinfo")[
        "hash_serialized_3"
    ]

    assert stats.digest[::-1].hex() == node_muhash
    assert _hash_serialized_3(utxo_set)[::-1].hex() == node_hash_serialized_3
