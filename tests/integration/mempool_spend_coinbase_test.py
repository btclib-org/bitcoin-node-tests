# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_spend_coinbase`, one body over either node.

Read from Core's `test/functional/mempool_spend_coinbase.py`
(`6eca11175be6`, 2026-07-16) rather than ported: that file starts from a
node the framework's own fixture already carries 200 blocks into, and
`invalidateblock`s two of them back off so that one specific coinbase
sits exactly `COINBASE_MATURITY` confirmations deep and its immediate
successor one short. This node starts at height zero, so the same pair
is reached without the invalidation: `MiniWallet.generate(COINBASE_MATURITY)`
leaves its own first-mined coin at the exact boundary and its second at
one confirmation short, `mini_wallet.py`'s own `get_utxo` naming either
one directly, maturity aside -- `mempool_spend_coinbase.py`'s own subject
is what the *node* does with the immature one, not a check the wallet
should make first.

`mempool_spend_coinbase_bitcoind_test.py` and
`mempool_spend_coinbase_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.block.block import Block
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["a_mature_coinbase_spends_and_an_immature_one_is_refused"]


def _txids(adapter: NodeAdapter, block_hash: bytes) -> list[str]:
    """Return the ids of `block_hash`'s own transactions, coinbase first.

    Read off `getblock`'s verbosity 0, the raw block: btclib-node serves
    that verbosity alone at the released build, refusing the JSON one
    Core's own file reads `tx` from.
    """
    block_hex = adapter.rpc.call("getblock", [block_hash.hex(), 0])
    block = Block.parse(bytes.fromhex(block_hex), check_validity=False)
    return [tx.id.hex() for tx in block.transactions]


def a_mature_coinbase_spends_and_an_immature_one_is_refused(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject: the node accepts one and refuses the other.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.MINE, adapter.capabilities, skip_counts)
    wallet = MiniWallet(adapter)
    hashes = wallet.generate(COINBASE_MATURITY)
    mature_coinbase_txid = _txids(adapter, hashes[0])[0]
    immature_coinbase_txid = _txids(adapter, hashes[1])[0]
    mature_coin = wallet.get_utxo(txid=mature_coinbase_txid)
    immature_coin = wallet.get_utxo(txid=immature_coinbase_txid)

    mature_tx = wallet.send_self_transfer(utxo_to_spend=mature_coin)
    immature_tx = wallet.create_self_transfer(utxo_to_spend=immature_coin)

    with pytest.raises(RpcError, match="bad-txns-premature-spend-of-coinbase"):
        adapter.rpc.call(
            "sendrawtransaction",
            [immature_tx.serialize(True, check_validity=False).hex()],
        )
    mempool = adapter.rpc.call("getrawmempool")
    assert mature_tx.id.hex() in mempool
    assert immature_tx.id.hex() not in mempool

    wallet.generate(1)  # one more block matures what was one confirmation short

    txid = adapter.rpc.call(
        "sendrawtransaction", [immature_tx.serialize(True, check_validity=False).hex()]
    )
    assert txid == immature_tx.id.hex()
