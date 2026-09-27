# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_rescan_unconfirmed`, one body over either node.

Read from Core's `test/functional/wallet_rescan_unconfirmed.py`
(`fa5f29774872`, 2025-12-16, the same file at the pinned `v31.1`): a
parent paying the wallet is mined, a child sweeping it to an address no
wallet holds sits in the mempool, and an `invalidateblock` puts the
parent back in the mempool after its child. A watch-only wallet
importing the parent's descriptor then finds both transactions in its
rescan of the mempool, the child only through its input, it paying the
wallet nothing. Every assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.INVALIDATE_BLOCK`, the reorg, and `Capability.MINE`, the
`MiniWallet` (`mini_wallet.py`) that pays the parent and mines it, of a
fresh node of the body's own. Core runs on its harness's cached chain,
in which `MiniWallet` already holds mature coins; this starts on a clean
chain and has `MiniWallet` mine until one of its coinbases matures,
before the test's own first step. Core's `generate` mines the mempool
node-side; `MiniWallet.generate`'s own `confirm` names the parent
instead. Core's `syncwithvalidationinterfacequeue` is bitcoind's own RPC
(`src/rpc/blockchain.cpp`), so it is called on bitcoind alone. Core's
`test_address` (`wallet_util.py`) is the `getaddressinfo` it wraps, and
`ADDRESS_BCRT1_UNSPENDABLE` (`address.py`) is btclib's: the regtest
pay-to-witness-script-hash address of an all-zero hash.

`wallet_rescan_unconfirmed_bitcoind_test.py` and
`wallet_rescan_unconfirmed_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.b32 import address_from_witness
from btclib.script.script_pub_key import ScriptPubKey
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["an_import_rescans_a_child_back_in_the_mempool_before_its_parent"]

# `messages.py`'s own `COIN`
_COIN = 100_000_000

# Core's `ADDRESS_BCRT1_UNSPENDABLE`
_UNSPENDABLE = address_from_witness(0, bytes(32), "regtest")


def _sync_validation_queue(node: BitcoindAdapter | BtclibNodeAdapter) -> None:
    """Core's `syncwithvalidationinterfacequeue`, on bitcoind alone."""
    if isinstance(node, BitcoindAdapter):
        node.rpc.call("syncwithvalidationinterfacequeue")


def an_import_rescans_a_child_back_in_the_mempool_before_its_parent(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    require(Capability.INVALIDATE_BLOCK, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    tester_wallet = MiniWallet(node)
    tester_wallet.generate(COINBASE_MATURITY + 1)

    node.rpc.call("createwallet", {"wallet_name": "w0", "disable_private_keys": False})
    w0 = node.rpc.for_wallet("w0")

    # a parent tx, mined in a block that will later be disconnected
    parent_address = w0.call("getnewaddress")
    parent = tester_wallet.send_to(ScriptPubKey.from_address(parent_address), _COIN)
    tx_parent_to_reorg = parent.id.hex()
    assert tx_parent_to_reorg in node.rpc.call("getrawmempool")
    block_to_reorg = tester_wallet.generate(1, confirm=[parent])[0].hex()
    assert len(node.rpc.call("getrawmempool")) == 0
    _sync_validation_queue(node)
    assert w0.call("gettransaction", [tx_parent_to_reorg])["confirmations"] == 1

    # an unconfirmed child of the parent, sending all of it to an
    # unspendable address: no change output, so only its input tells
    # a rescan it is the wallet's, and the parent must be seen first
    w0_utxos = w0.call("listunspent")

    # the only UTXO available to spend is tx_parent_to_reorg
    assert len(w0_utxos) == 1
    assert w0_utxos[0]["txid"] == tx_parent_to_reorg
    tx_child_unconfirmed_sweep = w0.call(
        "sendall", {"recipients": [_UNSPENDABLE], "options": {"locktime": 0}}
    )["txid"]
    assert tx_child_unconfirmed_sweep in node.rpc.call("getrawmempool")
    _sync_validation_queue(node)

    # a reorg puts the parent back in the mempool after its child
    node.rpc.call("invalidateblock", [block_to_reorg])
    assert tx_parent_to_reorg in node.rpc.call("getrawmempool")

    # the descriptor is ranged, so no label
    parent_desc = w0.call("getaddressinfo", [parent_address])["parent_desc"]
    node.rpc.call("createwallet", {"wallet_name": "w1", "disable_private_keys": True})
    w1 = node.rpc.for_wallet("w1")
    w1.call("importdescriptors", [[{"desc": parent_desc, "timestamp": 0}]])

    # the importing wallet has rescanned the mempool's transactions
    info = w1.call("getaddressinfo", [parent_address])
    assert info["solvable"] is True
    assert info["ismine"] is True
    # `gettransaction` refuses a transaction the rescan did not find
    assert w1.call("gettransaction", [tx_parent_to_reorg])["confirmations"] == 0
    assert w1.call("gettransaction", [tx_child_unconfirmed_sweep])["confirmations"] == 0
