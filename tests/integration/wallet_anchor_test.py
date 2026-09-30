# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_anchor`, one body over either node.

Read from Core's `test/functional/wallet_anchor.py` (`609d265ebc51`,
2025-09-03, the same file at the pinned `v31.1`): a zero-value
pay-to-anchor output, and its spend, are found by a watch-only wallet
importing the anchor's address only through a rescan of the blocks
holding them, `listunspent` naming the output until the rescan reaches
its spend. A wallet refuses to import the anchor where it holds private
keys, and one that holds it watch-only cannot spend it, refusing each
of `send`, `sendtoaddress` and `sendall`. Every assertion of Core's own
is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.MINE`, the `MiniWallet` (`mini_wallet.py`) that builds the
anchor and its spend, `Capability.GENERATE`, the `generateblock` and
`generatetoaddress` the body mines with, `Capability.CLOCK`, the
`setmocktime` that keeps the import's own rescan off the anchor's
blocks, and `Capability.PACKAGE_ACCEPTANCE`, the `submitpackage` taking
the anchor and its spend together, of a fresh node of the body's own.

Core runs on its harness's cached chain, whose coinbases
pay, among others, `MiniWallet` and the deterministic key its harness
imports into `default_wallet`. This starts on a clean chain instead,
before the test's own first step: it creates `default_wallet`, mines
one block to an address of its own, and has `MiniWallet` mine until
two coins of its own mature, the one block's coinbase maturing with
them. Core's `generate` pays that deterministic key; this mines to an
address of `default_wallet`'s own instead.

Core's clock moves to the wall clock plus `MAX_FUTURE_BLOCK_TIME` and a
second, so that an import stamped with the mocked time rescans from
past the anchor's blocks, the harness's cached blocks being older than
the wall clock. `MiniWallet` stamps each block it mines at least a
second past the last, so its chain runs ahead of the wall clock; this
moves the clock forward from the later of the wall clock and the chain's
own latest block time instead.

Core hands `sendall` the entries `listunspent` answered as its `inputs`;
this hands it each entry's `txid` and `vout`. Those, with a `sequence`
no entry carries, are what `AddInputs` (`src/rpc/rawtransaction_util.cpp`)
reads of an input, and `bitcoin_core_rpc` refuses the `Decimal` amount
an entry carries as a parameter.

`wallet_anchor_bitcoind_test.py` and `wallet_anchor_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from btclib.block.limits import MAX_FUTURE_BLOCK_TIME
from btclib.descriptors.descriptors import add_checksum
from btclib.script.engine import PAY_TO_ANCHOR
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx.limits import COINBASE_MATURITY
from btclib.tx.out_point import OutPoint
from btclib.tx.tx_in import TxIn
from btclib.tx.tx_out import TxOut

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from tests.integration.wallet_signmessagewithaddress_test import refused

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient
    from btclib.tx.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["a_wallet_sees_an_anchor_it_cannot_spend"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

# Core's `ANCHOR_ADDRESS` (`script_util.py`)
_ANCHOR_ADDRESS = ScriptPubKey(PAY_TO_ANCHOR, "regtest").address

# `src/rpc/protocol.h`: what `gettransaction` answers a txid the wallet
# does not hold, and what the wallet answers a spend it cannot make
_RPC_INVALID_ADDRESS_OR_KEY = -5
_RPC_WALLET_ERROR = -4

_NOT_THE_WALLETS = "Invalid or non-wallet transaction id"
_UNSOLVABLE = (
    "Unable to determine the size of the transaction, the wallet contains"
    " unsolvable descriptors"
)


def _hex(tx: Tx) -> str:
    """Return `tx` with its witness, as Core's own `serialize().hex()`."""
    return tx.serialize(True, check_validity=False).hex()


def _latest_block_time(node: BitcoindAdapter | BtclibNodeAdapter) -> int:
    """Return the latest time any block of `node`'s own chain carries."""
    latest = 0
    for height in range(node.rpc.call("getblockcount") + 1):
        block_hash = node.rpc.call("getblockhash", [height])
        block_time = node.rpc.call("getblockheader", [block_hash])["time"]
        assert isinstance(block_time, int)
        latest = max(latest, block_time)
    return latest


def _zero_value_anchor_listunspent(
    node: BitcoindAdapter | BtclibNodeAdapter,
    sender: MiniWallet,
    default_wallet: BitcoinCoreRpcClient,
) -> None:
    """Core's `test_0_value_anchor_listunspent`.

    0-value anchor outputs are detected as UTXOs.
    """
    # an anchor output, and its spend
    anchor_tx = sender.create_self_transfer(fee_rate=0, version=3)
    anchor_tx.vout.append(TxOut(0, PAY_TO_ANCHOR))
    anchor_spend = sender.create_self_transfer(version=3)
    anchor_spend.vin.append(
        TxIn(OutPoint(anchor_tx.id, 1), b"", 0, Witness(), check_validity=False)
    )
    submit_res = node.rpc.call("submitpackage", [[_hex(anchor_tx), _hex(anchor_spend)]])
    assert submit_res["package_msg"] == "success"
    anchor_txid = anchor_tx.id.hex()
    anchor_spend_txid = anchor_spend.id.hex()

    # each tx mined in a block of its own
    sender_address = sender.script_pub_key.address
    node.rpc.call("generateblock", [sender_address, [_hex(anchor_tx)]])
    anchor_tx_height = node.rpc.call("getblockcount")
    node.rpc.call("generateblock", [sender_address, [_hex(anchor_spend)]])

    # time mocked forward, and blocks mined, to avoid rescanning the latest
    now = max(int(time.time()), _latest_block_time(node))
    node.set_mock_time(now + MAX_FUTURE_BLOCK_TIME + 1)
    node.rpc.call("generatetoaddress", [10, default_wallet.call("getnewaddress")])

    node.rpc.call(
        "createwallet", {"wallet_name": "anchor", "disable_private_keys": True}
    )
    wallet = node.rpc.for_wallet("anchor")
    import_res = wallet.call(
        "importdescriptors",
        [[{"desc": add_checksum(f"addr({_ANCHOR_ADDRESS})"), "timestamp": "now"}]],
    )
    assert import_res[0]["success"] is True

    # the wallet has no UTXOs, and knows neither the anchor tx nor its spend
    assert wallet.call("listunspent") == []
    for txid in (anchor_txid, anchor_spend_txid):
        refused(
            wallet,
            "gettransaction",
            [txid],
            _RPC_INVALID_ADDRESS_OR_KEY,
            _NOT_THE_WALLETS,
        )

    # a rescan of the block holding the anchor makes listunspent list it
    wallet.call("rescanblockchain", [0, anchor_tx_height])
    utxos = wallet.call("listunspent")
    assert len(utxos) == 1
    assert utxos[0]["txid"] == anchor_txid
    assert utxos[0]["address"] == _ANCHOR_ADDRESS
    assert utxos[0]["amount"] == 0
    wallet.call("gettransaction", [anchor_txid])
    refused(
        wallet,
        "gettransaction",
        [anchor_spend_txid],
        _RPC_INVALID_ADDRESS_OR_KEY,
        _NOT_THE_WALLETS,
    )

    # a rescan of the rest of the chain sees the anchor spent
    wallet.call("rescanblockchain")
    assert wallet.call("listunspent") == []
    wallet.call("gettransaction", [anchor_spend_txid])


def _cannot_sign_anchors(
    node: BitcoindAdapter | BtclibNodeAdapter,
    default_wallet: BitcoinCoreRpcClient,
) -> None:
    """Core's `test_cannot_sign_anchors`: the wallet cannot spend anchors."""
    for disable_privkeys in [False, True]:
        name = f"anchor_spend_{disable_privkeys}"
        node.rpc.call(
            "createwallet",
            {"wallet_name": name, "disable_private_keys": disable_privkeys},
        )
        wallet = node.rpc.for_wallet(name)
        import_res = wallet.call(
            "importdescriptors",
            [
                [
                    {
                        "desc": add_checksum(f"addr({_ANCHOR_ADDRESS})"),
                        "timestamp": "now",
                    },
                    {
                        "desc": add_checksum(f"raw({PAY_TO_ANCHOR.hex()})"),
                        "timestamp": "now",
                    },
                ]
            ],
        )
        assert import_res[0]["success"] is disable_privkeys
        assert import_res[1]["success"] is disable_privkeys

    anchor_txid = default_wallet.call("sendtoaddress", [_ANCHOR_ADDRESS, 1])
    node.rpc.call("generatetoaddress", [1, default_wallet.call("getnewaddress")])

    wallet = node.rpc.for_wallet("anchor_spend_True")
    utxos = wallet.call("listunspent")
    assert len(utxos) == 1
    assert utxos[0]["txid"] == anchor_txid
    assert utxos[0]["address"] == _ANCHOR_ADDRESS
    assert utxos[0]["amount"] == 1

    refused(
        wallet,
        "send",
        [[{default_wallet.call("getnewaddress"): 0.9999}]],
        _RPC_WALLET_ERROR,
        "Missing solving data for estimating transaction size",
    )
    refused(
        wallet,
        "sendtoaddress",
        [default_wallet.call("getnewaddress"), 0.9999],
        _RPC_WALLET_ERROR,
        "Error: Private keys are disabled for this wallet",
    )
    inputs = [{"txid": utxo["txid"], "vout": utxo["vout"]} for utxo in utxos]
    refused(
        wallet,
        "sendall",
        {"recipients": [default_wallet.call("getnewaddress")], "inputs": inputs},
        _RPC_WALLET_ERROR,
        _UNSOLVABLE,
    )
    refused(
        wallet,
        "sendall",
        {"recipients": [default_wallet.call("getnewaddress")]},
        _RPC_WALLET_ERROR,
        _UNSOLVABLE,
    )


def a_wallet_sees_an_anchor_it_cannot_spend(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)
    require(Capability.PACKAGE_ACCEPTANCE, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    default_wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call("generatetoaddress", [1, default_wallet.call("getnewaddress")])
    sender = MiniWallet(node)
    sender.generate(COINBASE_MATURITY + 1)

    _zero_value_anchor_listunspent(node, sender, default_wallet)
    _cannot_sign_anchors(node, default_wallet)
