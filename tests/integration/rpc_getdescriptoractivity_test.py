# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptoractivity`, one body over either node.

Read from Core's `test/functional/rpc_getdescriptoractivity.py`
(`3fd68a95e68b`, 2026-04-07) and narrowed to what the MiniWallet family
reaches
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`MiniWallet.send_to` (`Capability.MINE`) pays a fresh address this module
builds -- `getnewdestination` (`wallet.py`) has no counterpart here, so a
key-path p2tr output over a random key this module generates itself,
the output `getnewdestination` builds by default, is what stands in for
it.
`Capability.DESCRIPTOR_ACTIVITY` gates every subject here, ahead of
`Capability.MINE` where a subject asks for both.

The subjects paying `_AMOUNT` each start a node of their own, from the
cluster they are handed, as Core's own file sets `setup_clean_chain`
ahead of paying the same fixed 1 BTC. `MiniWallet.send_to` spends the
largest coinbase the subject's own wallet has matured, and on the
session's shared adapter that coinbase is mined on top of whatever
chain the tests before it left: past enough regtest halvings, it is
worth less than `_AMOUNT`
([ISS 127](https://github.com/btclib-org/bitcoin-node-tests/issues/127)).

Not the clock family, unlike Core's own file: Core's own `setmocktime`
call there freezes the clock its own node-driven mining
(`generatetodescriptor`) reads block times from, ahead of `self.generate
(wallet, 200)` -- `feature_utxo_set_hash_test.py`'s own
docstring is where the same measurement is made in full, against the
same MiniWallet-mined chain: freezing this harness's own node's clock
ahead of a `MiniWallet.generate` call, which always builds a block's own
time from the wall clock rather than reading the node's, produces a
`time-too-new` refusal rather than the freeze Core's own file relies on.

None of Core's own subtests is dropped: kept is that an unused address
carries no activity; that a payment confirmed in a named block makes the
answer's only key `activity` and reports one `receive` entry, checked
for its `type`, `blockhash`, `height`, `txid`, `vout` and `amount` and
for its `output_spk`'s `hex`, `address`, `type`, the witness version
opening its `asm` and the `rawtr` function opening its `desc`; that an
unconfirmed payment is excluded when `include_mempool` is `False`; and
the RPC-argument errors (`Block not found`, an invalid descriptor, and
the required-argument usage string). Kept too
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)):
Core's own multiple-address query, its mix of a confirmed and an
unconfirmed payment, its receive-then-spend over two blocks, and its
no-address case, a coin paying `mini_wallet.py`'s
`RAW_P2PK_SCRIPT_PUB_KEY`, Core's own `RAW_P2PK` output, spent under
`raw_p2pk_script_sig`. Each of these confirms its transactions in a
block `_mine` builds, whose coinbase pays a fresh key-path p2tr output
rather than `MiniWallet`'s own script, as Core's own `self.generate
(node, 1)` pays the node's own address: a coinbase paying the queried
script would be activity of its own. The receive-then-spend query is
also asked with its two blocks reversed, as Core's own comment says it
is, where Core's own call repeats them in their original order.

`rpc_getdescriptoractivity_bitcoind_test.py` and
`rpc_getdescriptoractivity_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.key import PubKeyData
from btclib.script.script_pub_key import ScriptPubKey
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY
from btclib_ecc.curves.curve import mult
from btclib_ecc.curves.sec_point import bytes_from_point
from btclib_wallet.descriptors.descriptors import add_checksum

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import (
    FEE,
    RAW_P2PK_SCRIPT_PUB_KEY,
    MiniWallet,
    build_next_block,
    raw_p2pk_script_sig,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.block.block import Block

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter


__all__ = [
    "activity_in_block",
    "confirmed_and_unconfirmed",
    "invalid_blockhash",
    "invalid_descriptor",
    "multiple_addresses",
    "no_activity_for_an_unused_address",
    "no_address",
    "no_mempool_inclusion",
    "receive_then_spend",
    "required_args",
]

_AMOUNT = 100_000_000  # 1 BTC, satoshi


def _random_p2tr(network: str) -> ScriptPubKey:
    """Return a fresh key-path p2tr output, for `getnewdestination`."""
    point = mult(secrets.randbelow(2**256))
    key = PubKeyData(bytes_from_point(point), network=network)
    return ScriptPubKey.p2tr(key, network=network)


def _raw_descriptor(script_pub_key: ScriptPubKey) -> str:
    """Return `raw(<hex>)` with its checksum, Core's own `get_descriptor`."""
    return add_checksum(f"raw({script_pub_key.script.hex()})")


def _mine(
    node: NodeAdapter,
    transactions: tuple[Tx, ...] = (),
    script_pub_key: ScriptPubKey | None = None,
) -> Block:
    """Mine one block carrying `transactions` onto `node`'s own tip.

    Its coinbase pays `script_pub_key`, a fresh key-path p2tr output where
    `None` -- this module's own docstring has why not `MiniWallet`'s.
    """
    block = build_next_block(
        node, script_pub_key or _random_p2tr("regtest"), transactions
    )
    answer = node.rpc.call("submitblock", [block.serialize(check_validity=False).hex()])
    assert answer is None
    return block


def _satoshi(amount: object) -> int:
    """Return an RPC's own BTC `amount` in satoshis."""
    return round(float(str(amount)) * 100_000_000)


def no_activity_for_an_unused_address(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check an address nothing ever paid carries no activity.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.DESCRIPTOR_ACTIVITY, adapter.capabilities, skip_counts)
    addr = _random_p2tr("regtest").address
    result = adapter.rpc.call("getdescriptoractivity", [[], [f"addr({addr})"], True])
    assert result["activity"] == []


def activity_in_block(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a payment confirmed in a named block reports one receive entry.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    spk = _random_p2tr("regtest")
    tx = wallet.send_to(spk, _AMOUNT)
    (block_hash,) = wallet.generate(1, confirm=[tx])

    height = node.rpc.call("getblockheader", [block_hash.hex()])["height"]

    result = node.rpc.call(
        "getdescriptoractivity", [[block_hash.hex()], [f"addr({spk.address})"], True]
    )
    assert list(result.keys()) == ["activity"]
    (activity,) = result["activity"]
    assert activity["type"] == "receive"
    assert activity["blockhash"] == block_hash.hex()
    assert activity["height"] == height
    assert activity["txid"] == tx.id.hex()
    assert activity["vout"] == 1  # send_to's own second output
    assert float(activity["amount"]) == _AMOUNT / 100_000_000
    output_spk = activity["output_spk"]
    assert output_spk["asm"][:2] == "1 "  # witness version 1
    assert output_spk["desc"].split("(")[0] == "rawtr"
    assert output_spk["hex"] == spk.script.hex()
    assert output_spk["address"] == spk.address
    assert output_spk["type"] == "witness_v1_taproot"


def no_mempool_inclusion(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check an unconfirmed payment is excluded when include_mempool is False.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    spk = _random_p2tr("regtest")
    wallet.send_to(spk, _AMOUNT)

    result = node.rpc.call(
        "getdescriptoractivity", [[], [f"addr({spk.address})"], False]
    )
    assert result["activity"] == []


def invalid_blockhash(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check an unknown blockhash is refused, not answered empty.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.DESCRIPTOR_ACTIVITY, adapter.capabilities, skip_counts)
    addr = _random_p2tr("regtest").address
    with pytest.raises(RpcError, match="Block not found"):
        adapter.rpc.call(
            "getdescriptoractivity", [["00" * 32], [f"addr({addr})"], True]
        )


def invalid_descriptor(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check an invalid descriptor function is refused.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.DESCRIPTOR_ACTIVITY, adapter.capabilities, skip_counts)
    with pytest.raises(RpcError, match="is not a valid descriptor"):
        adapter.rpc.call("getdescriptoractivity", [[], ["addrx(x)"], True])


def required_args(
    adapter: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """Check calling with too few arguments is refused with the usage string.

    :param adapter: `bitcoind_adapter` or `btclib_node_adapter`.
    :param skip_counts: the session's own tally.
    """
    require(Capability.DESCRIPTOR_ACTIVITY, adapter.capabilities, skip_counts)
    with pytest.raises(RpcError, match="getdescriptoractivity"):
        adapter.rpc.call("getdescriptoractivity")
    with pytest.raises(RpcError, match="getdescriptoractivity"):
        adapter.rpc.call("getdescriptoractivity", [[]])


def multiple_addresses(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check several addresses, duplicated or reordered, answer alike.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    spk_1, spk_2 = _random_p2tr("regtest"), _random_p2tr("regtest")
    tx_1 = wallet.send_to(spk_1, _AMOUNT)
    tx_2 = wallet.send_to(spk_2, 2 * _AMOUNT)
    blockhash = _mine(node, (tx_1, tx_2)).header.hash.hex()
    addr_1, addr_2 = f"addr({spk_1.address})", f"addr({spk_2.address})"

    result = node.rpc.call(
        "getdescriptoractivity", [[blockhash], [addr_1, addr_2], True]
    )
    assert len(result["activity"]) == 2
    duplicated = [[blockhash], [addr_1, addr_1, addr_2], True]
    assert node.rpc.call("getdescriptoractivity", duplicated) == result
    flipped = [[blockhash], [addr_2, addr_1], True]
    assert node.rpc.call("getdescriptoractivity", flipped) == result

    by_address = {a["output_spk"]["address"]: a for a in result["activity"]}
    assert by_address[spk_1.address]["blockhash"] == blockhash
    assert _satoshi(by_address[spk_1.address]["amount"]) == _AMOUNT
    assert by_address[spk_2.address]["blockhash"] == blockhash
    assert _satoshi(by_address[spk_2.address]["amount"]) == 2 * _AMOUNT


def confirmed_and_unconfirmed(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a confirmed payment carries its block; an unconfirmed one does not.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    spk_1, spk_2 = _random_p2tr("regtest"), _random_p2tr("regtest")
    tx_1 = wallet.send_to(spk_1, _AMOUNT)
    blockhash = _mine(node, (tx_1,)).header.hash.hex()
    tx_2 = wallet.send_to(spk_2, _AMOUNT)

    descriptors = [f"addr({spk_1.address})", f"addr({spk_2.address})"]
    result = node.rpc.call("getdescriptoractivity", [[blockhash], descriptors, True])
    activity = result["activity"]
    assert len(activity) == 2

    (confirmed,) = [a for a in activity if a.get("blockhash") == blockhash]
    assert confirmed["txid"] == tx_1.id.hex()
    assert confirmed["height"] == node.rpc.call("getblockchaininfo")["blocks"]

    (unconfirmed,) = [a for a in activity if not a.get("blockhash")]
    assert "blockhash" not in unconfirmed
    assert "height" not in unconfirmed
    assert unconfirmed["txid"] == tx_2.id.hex()


def receive_then_spend(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a coin received in one block and spent in the next.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)

    sent_1 = wallet.send_self_transfer()
    utxo = wallet.get_utxo(txid=sent_1.id.hex())
    blockhash_1 = _mine(node, (sent_1,)).header.hash.hex()
    sent_2 = wallet.send_self_transfer(utxo_to_spend=utxo)
    blockhash_2 = _mine(node, (sent_2,)).header.hash.hex()

    descriptor = _raw_descriptor(wallet.script_pub_key)
    request = [[blockhash_1, blockhash_2], [descriptor], True]
    result = node.rpc.call("getdescriptoractivity", request)
    assert len(result["activity"]) == 4

    receive = result["activity"][1]
    assert receive["type"] == "receive"
    assert receive["txid"] == sent_1.id.hex()
    assert receive["blockhash"] == blockhash_1

    spend = result["activity"][2]
    assert spend["type"] == "spend"
    assert spend["spend_txid"] == sent_2.id.hex()
    assert spend["spend_vin"] == 0
    assert spend["prevout_txid"] == sent_1.id.hex()
    assert spend["blockhash"] == blockhash_2

    reversed_order = [[blockhash_2, blockhash_1], [descriptor], True]
    assert node.rpc.call("getdescriptoractivity", reversed_order) == result
    duplicated = [[blockhash_1, blockhash_2, blockhash_2], [descriptor], True]
    assert node.rpc.call("getdescriptoractivity", duplicated) == result


def no_address(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a script with no address still reports its spend and its receive.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DESCRIPTOR_ACTIVITY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    coinbase = _mine(node, script_pub_key=RAW_P2PK_SCRIPT_PUB_KEY).transactions[0]
    MiniWallet(node).generate(COINBASE_MATURITY)

    coin_value = coinbase.vout[0].value
    tx_out = TxOut(coin_value - FEE, RAW_P2PK_SCRIPT_PUB_KEY)
    unsigned = Tx(
        version=2, lock_time=0, vin=[TxIn(OutPoint(coinbase.id, 0))], vout=[tx_out]
    )
    tx_in = TxIn(OutPoint(coinbase.id, 0), script_sig=raw_p2pk_script_sig(unsigned, 0))
    spend_tx = Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out])
    blockhash = _mine(node, (spend_tx,)).header.hash.hex()

    descriptor = _raw_descriptor(RAW_P2PK_SCRIPT_PUB_KEY)
    result = node.rpc.call("getdescriptoractivity", [[blockhash], [descriptor], False])
    spend, receive = result["activity"]

    assert spend["type"] == "spend"
    assert spend["blockhash"] == blockhash
    assert list(spend["prevout_spk"].keys()) == ["asm", "desc", "hex", "type"]
    assert _satoshi(spend["amount"]) == coin_value

    assert receive["type"] == "receive"
    assert receive["blockhash"] == blockhash
    assert list(receive["output_spk"].keys()) == ["asm", "desc", "hex", "type"]
    assert _satoshi(receive["amount"]) == coin_value - FEE
