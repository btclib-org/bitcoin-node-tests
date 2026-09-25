# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`MiniWallet`: coins without a wallet, cached from blocks it mines itself.

[ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4), step 5
of [ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220):
Core's own `MiniWallet` (`test/functional/test_framework/wallet.py`) feeds
its own cache by calling `generatetodescriptor` and then `scantxoutset` --
mining through the node's descriptor-wallet machinery and asking the node
to find its own coins back. This one needs neither RPC: `generate` builds
the coinbase itself (`btclib.block.build.build_coinbase`), mines it
(`btclib.block.mining.mine`) and delivers it over `submitblock`, so the
txid and the vout its own coin sits at are known before the block is ever
submitted rather than scanned back out of the node afterwards.

The scriptPubKey every coin of this class pays is Core's own default
`MiniWalletMode.ADDRESS_OP_TRUE` (`wallet.py`'s own docstring table): a
P2TR output whose internal key is the x-only integer 1 and whose single
tapscript leaf, at leaf version `0xc0`, is bare `OP_TRUE` -- the same
pair `test_framework/address.py`'s own
`create_deterministic_address_bcrt1_p2tr_op_true` and
`test_framework/script.py`'s own `taproot_construct` build.
`btclib.script.taproot.output_pubkey` and
`input_script_sig` build the same output key and the same control block
from that pair, byte for byte: the address this module's own scriptPubKey
serializes to under `regtest` is Core's own published constant,
`bcrt1p9yfmy5h72durp7zrhlw9lf7jpwjgvwdg0jr0lqmmjtgg83266lqsekaqka`, and
the spend it proves is standard under bitcoind's default mempool policy,
needing neither a scriptSig long enough to clear a minimum size nor a
policy flag to admit a scriptPubKey no standard template matches. `OP_TRUE`
alone is still the smaller claim than a real signature (`RAW_P2PK`,
`wallet.py`'s third mode): it proves the mechanism this issue is about --
a cache fed from mined blocks -- without also proving btclib's own
signing surface, which every other module of this suite already leaves to
btclib's own test suite (rule 7,
[ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220)).

`Capability.MINE` is what a caller checks before constructing one, the
same capability the first family already skips on for a node not
mining: not a new one, since this class produces the fact `MINE` already
names -- "a block the node accepts as its own new tip, however it gets
there" -- by client-side construction over `submitblock` rather than a
node's own wallet, exactly the second half `node.py`'s own docstring
already draws. `TF2.md`'s own per-test ledger has why no node other than
bitcoind runs a `MiniWallet` test today: `BtclibNodeAdapter` does not
declare it, and no way of delivering a solved block -- `submitblock` or
the wire -- reaches around the reason, ISS btclib-node#1071 being about
the node's own state machine and not about how a block arrives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.alias import TaprootScriptTree
from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS, subsidy
from btclib.key import PubKeyData
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.taproot import input_script_sig
from btclib.script.taproot import serialize as tapscript_serialize
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

if TYPE_CHECKING:
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "FEE",
    "MiniWallet",
    "Utxo",
]

# Core's own ADDRESS_OP_TRUE internal key (`test_framework/address.py`'s
# own `create_deterministic_address_bcrt1_p2tr_op_true`): the x-only
# integer 1, prefixed 02 for `PubKeyData` -- the prefix names the lift as
# BIP341's own even one and adds nothing the tweak reads
_INTERNAL_PUBKEY = PubKeyData(b"\x02" + (1).to_bytes(32, "big"), check_validity=False)

# the single tapscript leaf ADDRESS_OP_TRUE carries -- leaf version 0xc0,
# Core's own `taproot_construct` default -- bare OP_TRUE, needing no
# signature and proving Core's own script path rather than its key path
_SCRIPT_TREE: TaprootScriptTree = [(0xC0, ["OP_TRUE"])]

# the anyone-can-spend P2TR output every coin of this class pays;
# `regtest`, this module's only chain, decides the address the taproot
# output key serializes to and nothing about the output key itself
_ANYONE_CAN_SPEND = ScriptPubKey.p2tr(_INTERNAL_PUBKEY, _SCRIPT_TREE, network="regtest")

# satoshis, a fixed fee: this class asks the node for nothing to compute
# one, the same shape Core's own `send_to` (`wallet.py`) takes and for
# the same reason
FEE = 1000

# regtest's own halving schedule (`CONSENSUS_PARAMS["regtest"]`): every 150
# blocks rather than mainnet's 210_000, `subsidy`'s own default -- this
# module's only chain, so `generate` reads this rather than that default
_REGTEST_SUBSIDY_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval


@dataclass(frozen=True)
class Utxo:
    """One coin `MiniWallet` knows about, spendable with `_witness()` alone."""

    outpoint: OutPoint
    value: int
    height: int
    coinbase: bool


def _witness() -> Witness:
    """Return the script-path witness that spends `_ANYONE_CAN_SPEND`.

    `input_script_sig` returns the one leaf and the control block that
    proves it against the output key; the witness stack is the leaf
    script serialized (BIP342's `serialize`, not the ordinary script
    codec, `_SCRIPT_TREE` carrying no `OP_SUCCESS` this call would need
    to differ on) followed by the control block, per BIP341.
    """
    leaf_script, control_block = input_script_sig(_INTERNAL_PUBKEY, _SCRIPT_TREE, 0)
    return Witness([tapscript_serialize(leaf_script), control_block])


class MiniWallet:
    """Coins without a wallet: a UTXO cache fed from blocks this class mines.

    This module's own docstring is the design; `Capability.MINE`
    (`capability.py`) is what a caller checks before constructing one.

    :param node: the node this wallet mines into and spends against, its
        `rpc` the whole of how this class ever reaches it -- no
        in-process import of anything the node itself runs.
    """

    def __init__(self, node: NodeAdapter) -> None:
        self._node = node
        self._utxos: list[Utxo] = []
        best_hash = node.rpc.call("getbestblockhash")
        if not isinstance(best_hash, str):
            err_msg = f"getbestblockhash answered {best_hash!r}, not a hash string"
            raise TypeError(err_msg)
        self._tip = bytes.fromhex(best_hash)
        height = node.rpc.call("getblockcount")
        if not isinstance(height, int):
            err_msg = f"getblockcount answered {height!r}, not an int"
            raise TypeError(err_msg)
        self._height = height
        chain_info = node.rpc.call("getblockchaininfo")
        median_time = (
            chain_info.get("mediantime") if isinstance(chain_info, dict) else None
        )
        if not isinstance(median_time, int):
            err_msg = f"getblockchaininfo answered {chain_info!r}, no int mediantime"
            raise TypeError(err_msg)
        # seeded from the existing chain's own median-time-past rather than
        # 0: a node this wallet did not mine into -- the session-scoped
        # `bitcoind_adapter` fixture hands more than one MiniWallet the same
        # node -- already has a tip whose median-time-past this wallet's
        # first block must exceed, `time-too-old` otherwise
        self._last_time = median_time

    @property
    def script_pub_key(self) -> ScriptPubKey:
        """Return the anyone-can-spend script every coin of this wallet pays."""
        return _ANYONE_CAN_SPEND

    def get_balance(self) -> int:
        """Return the satoshi sum of every coin this wallet still holds."""
        return sum(utxo.value for utxo in self._utxos)

    def generate(self, count: int) -> list[bytes]:
        """Mine `count` blocks paying this wallet's own script, and cache them.

        Client-side start to finish: `build_coinbase` and `build_block`
        (`btclib.block.build`) build the block, `mine`
        (`btclib.block.mining`) solves its nonce, and `submitblock`
        delivers it -- this module's own docstring has why nothing here
        ever calls `scantxoutset`. The block's own time is strictly
        later than the last one this call or a previous one produced, and
        than the chain's own median-time-past at construction: bitcoind
        refuses `time-too-old` for a block whose own time does not exceed
        its chain's own median-time-past, which two blocks minted in the
        same wall-clock second otherwise both carry, and which a second
        wallet built on top of a chain it did not itself mine otherwise
        carries from its very first block.

        :param count: how many blocks to mine.
        :returns: the mined blocks' own header hashes, display order,
            oldest first.
        :raises RuntimeError: `mine` exhausted its own search bound
            without solving one -- regtest's own target is wide enough
            that this is not expected to happen.
        :raises TypeError: `submitblock` answered anything but
            acceptance (`None`).
        """
        hashes = []
        for _ in range(count):
            height = self._height + 1
            coinbase = build_coinbase(
                height,
                _ANYONE_CAN_SPEND,
                halving_interval=_REGTEST_SUBSIDY_HALVING_INTERVAL,
            )
            block_time = max(int(datetime.now(UTC).timestamp()), self._last_time + 1)
            candidate = build_block(
                self._tip,
                [coinbase],
                datetime.fromtimestamp(block_time, UTC),
                REGTEST_POW_LIMIT_BITS,
            )
            solved = mine(candidate.header)
            if solved is None:
                err_msg = f"no nonce solved height {height} within the search bound"
                raise RuntimeError(err_msg)
            block = Block(solved, candidate.transactions, check_validity=False)
            answer = self._node.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
            if answer is not None:
                err_msg = f"submitblock refused height {height}: {answer!r}"
                raise TypeError(err_msg)
            self._utxos.append(
                Utxo(
                    outpoint=OutPoint(coinbase.id, 0),
                    value=subsidy(height, _REGTEST_SUBSIDY_HALVING_INTERVAL),
                    height=height,
                    coinbase=True,
                )
            )
            self._tip = block.header.hash
            self._height = height
            self._last_time = block_time
            hashes.append(self._tip)
        return hashes

    def _pop_mature_utxo(self) -> Utxo:
        """Return and forget the first matured coin this wallet still holds.

        Matured: a coinbase spent at `self._height + 1` -- the earliest
        height a transaction broadcast now could be mined at -- clears
        `COINBASE_MATURITY`, the same threshold Core's own `get_utxo`
        (`wallet.py`) applies for the same reason. A non-coinbase coin,
        which this class never yet produces, would need none of it.

        :raises LookupError: no coin of this wallet has matured yet.
        """
        for index, utxo in enumerate(self._utxos):
            spend_height = self._height + 1
            if not utxo.coinbase or spend_height - utxo.height >= COINBASE_MATURITY:
                return self._utxos.pop(index)
        err_msg = "no coin of this wallet has matured yet"
        raise LookupError(err_msg)

    def create_self_transfer(self) -> Tx:
        """Return an unbroadcast tx spending one matured coin, paid to itself.

        `send_self_transfer` is the caller wanting it broadcast too.

        :raises LookupError: no coin of this wallet has matured yet.
        """
        utxo = self._pop_mature_utxo()
        tx_in = TxIn(
            utxo.outpoint,
            script_sig=b"",
            sequence=0xFFFFFFFE,
            script_witness=_witness(),
        )
        tx_out = TxOut(utxo.value - FEE, _ANYONE_CAN_SPEND)
        tx = Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out])
        self._utxos.append(
            Utxo(
                outpoint=OutPoint(tx.id, 0),
                value=tx_out.value,
                height=0,
                coinbase=False,
            )
        )
        return tx

    def send_self_transfer(self) -> Tx:
        """Create, broadcast and cache a self-transfer; return the sent tx.

        The new coin `create_self_transfer` already cached is spendable
        the moment this returns: unlike a coinbase, `_pop_mature_utxo`
        never holds a non-coinbase coin back.

        :raises LookupError: no coin of this wallet has matured yet.
        :raises TypeError: `sendrawtransaction` answered something other
            than the sent tx's own id.
        """
        tx = self.create_self_transfer()
        tx_hex = tx.serialize(True, check_validity=False).hex()
        txid = self._node.rpc.call("sendrawtransaction", [tx_hex])
        if txid != tx.id.hex():
            err_msg = f"sendrawtransaction answered {txid!r}, not {tx.id.hex()!r}"
            raise TypeError(err_msg)
        return tx
