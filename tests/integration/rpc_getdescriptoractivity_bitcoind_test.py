# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptoractivity`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getdescriptoractivity.py`
(`3fd68a95e68b`, 2026-04-07) and narrowed to what the MiniWallet family
reaches
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`MiniWallet.send_to` (`Capability.MINE`) pays a fresh address this module
builds -- `getnewdestination` (`wallet.py`) has no counterpart here, so a
key-path p2tr output over a random key this module generates itself,
the output `getnewdestination` builds by default, is what stands in for
it, this suite's own signing surface being left to btclib's own test
suite the way `mini_wallet.py`'s own docstring already draws that line.
`Capability.DESCRIPTOR_ACTIVITY` gates every subject here, ahead of
`Capability.MINE` where a subject asks for both.

Not the clock family, unlike Core's own file: Core's own `setmocktime`
call there freezes the clock its own node-driven mining
(`generatetodescriptor`) reads block times from, ahead of `self.generate
(wallet, 200)` -- `feature_utxo_set_hash_bitcoind_test.py`'s own
docstring is where the same measurement is made in full, against the
same MiniWallet-mined chain: freezing this harness's own node's clock
ahead of a `MiniWallet.generate` call, which always builds a block's own
time from the wall clock rather than reading the node's, produces a
`time-too-new` refusal rather than the freeze Core's own file relies on.

A smaller claim than Core's own file: kept is that an unused address
carries no activity; that a payment confirmed in a named block makes the
answer's only key `activity` and reports one `receive` entry, checked
for its `type`, `blockhash`, `height`, `txid`, `vout` and `amount` and
for its `output_spk`'s `hex`, `address`, `type`, the witness version
opening its `asm` and the `rawtr` function opening its `desc`; that an
unconfirmed payment is excluded when `include_mempool` is `False`; and
the RPC-argument errors (`Block not found`, an invalid descriptor, and
the required-argument usage string). Dropped is Core's own
multiple-address query, its receive-then-spend, its mix of a confirmed
and an unconfirmed payment, and its no-address (`RAW_P2PK`) case, the
last needing a wallet mode this repository's own `MiniWallet` does not
build: it builds only Core's `ADDRESS_OP_TRUE` mode (`mini_wallet.py`'s
own docstring).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.curves.curve import mult
from btclib.curves.sec_point import bytes_from_point
from btclib.key import PubKeyData
from btclib.script.script_pub_key import ScriptPubKey
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

_AMOUNT = 100_000_000  # 1 BTC, satoshi


def _random_p2tr(network: str) -> ScriptPubKey:
    """Return a fresh key-path p2tr output, for `getnewdestination`."""
    point = mult(secrets.randbelow(2**256))
    key = PubKeyData(bytes_from_point(point), network=network)
    return ScriptPubKey.p2tr(key, network=network)


def test_no_activity_for_an_unused_address(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An address nothing ever paid carries no activity."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    addr = _random_p2tr("regtest").address
    result = bitcoind_adapter.rpc.call(
        "getdescriptoractivity", [[], [f"addr({addr})"], True]
    )
    assert result["activity"] == []


def test_activity_in_block(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """A payment confirmed in a named block reports one receive entry."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    spk = _random_p2tr("regtest")
    tx = wallet.send_to(spk, _AMOUNT)
    (block_hash,) = wallet.generate(1, confirm=[tx])

    height = bitcoind_adapter.rpc.call("getblockheader", [block_hash.hex()])["height"]

    result = bitcoind_adapter.rpc.call(
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


def test_no_mempool_inclusion(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An unconfirmed payment is excluded when include_mempool is False."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    spk = _random_p2tr("regtest")
    wallet.send_to(spk, _AMOUNT)

    result = bitcoind_adapter.rpc.call(
        "getdescriptoractivity", [[], [f"addr({spk.address})"], False]
    )
    assert result["activity"] == []


def test_invalid_blockhash(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An unknown blockhash is refused rather than silently answered empty."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    addr = _random_p2tr("regtest").address
    with pytest.raises(RpcError, match="Block not found"):
        bitcoind_adapter.rpc.call(
            "getdescriptoractivity", [["00" * 32], [f"addr({addr})"], True]
        )


def test_invalid_descriptor(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An invalid descriptor function is refused."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    with pytest.raises(RpcError, match="is not a valid descriptor"):
        bitcoind_adapter.rpc.call("getdescriptoractivity", [[], ["addrx(x)"], True])


def test_required_args(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Calling with too few arguments is refused with the usage string."""
    require(Capability.DESCRIPTOR_ACTIVITY, bitcoind_adapter.capabilities, skip_counts)
    with pytest.raises(RpcError, match="getdescriptoractivity"):
        bitcoind_adapter.rpc.call("getdescriptoractivity")
    with pytest.raises(RpcError, match="getdescriptoractivity"):
        bitcoind_adapter.rpc.call("getdescriptoractivity", [[]])
