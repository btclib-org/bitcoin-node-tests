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

[ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4)'s own
remaining ports add several things beyond the mechanism above. Two are
read off Core's own `wallet.py` rather than invented: `get_utxo` finds a
specific cached coin by its own txid, with no maturity filter -- a caller
naming one by hand is presumed to know what it is asking for,
`mempool_spend_coinbase.py`'s own subject being what a *node* does with an
immature one; `create_self_transfer` and `send_self_transfer` both take an
optional `utxo_to_spend`, spending the named coin in place of the next
automatically matured one. The other two have no counterpart there.
`resync` re-reads this wallet's own tip, height and median-time the way
`__init__` does, for a chain an `invalidateblock` or a `build_fork`
submission moved without this wallet's own `generate` doing it.
`rescan_utxos` (`wallet.py`) is the shape not taken: it also rebuilds the
coin cache from `scantxoutset`, which this module's own docstring already
has why nothing here ever calls; `resync` moves only the tip a `generate`
after it needs, leaving `_utxos` for the caller to reconcile against
whatever the RPC that exposed the reorg already told it.

`generate`'s own `confirm` is the second: no Core file has it, because
Core's own node-side mining (`generatetodescriptor`) pulls the whole
mempool into whatever it mines, and this class's mining reads no mempool
back to do the same (this module's own docstring already has why). A
caller that broadcast a transaction and wants it mined names it here,
already knowing it -- `send_self_transfer`'s own return value, typically
-- rather than this class fetching `getrawmempool` and
`getrawtransaction` back to rediscover what it already handed the node.

`build_fork`, alongside the class, is `create_empty_fork`
(`test/functional/test_framework/blocktools.py`): unsubmitted blocks
extending whatever tip the node it is given actually has, for a caller
that wants to hold them back and submit them later, `mempool_resurrect.py`'s
own subject. It shares no wallet state -- a fork is disposable by
construction, spent by nobody -- so it reads the node fresh rather than a
`MiniWallet` instance's own cache, and pays whichever `script_pub_key` its
caller names, that caller's own wallet's `script_pub_key` ordinarily.
"""

from __future__ import annotations

from collections.abc import Sequence
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
from btclib.script.script import serialize as script_serialize
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
    "build_fork",
    "nulldata_script_pub_key",
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


def _read_tip(node: NodeAdapter) -> tuple[bytes, int, int]:
    """Return `(tip, height, median_time)`, read fresh off `node`'s own RPC.

    Shared by the constructor, `MiniWallet.resync` and `build_fork`: each
    needs to know where the chain actually is right now rather than
    trusting a cached view that an out-of-band `invalidateblock` or a
    `build_fork` submission may have moved since it was last read.

    :param node: the node to read.
    :raises TypeError: `getbestblockhash`, `getblockcount` or
        `getblockchaininfo` answered something this call cannot use.
    """
    best_hash = node.rpc.call("getbestblockhash")
    if not isinstance(best_hash, str):
        err_msg = f"getbestblockhash answered {best_hash!r}, not a hash string"
        raise TypeError(err_msg)
    height = node.rpc.call("getblockcount")
    if not isinstance(height, int):
        err_msg = f"getblockcount answered {height!r}, not an int"
        raise TypeError(err_msg)
    chain_info = node.rpc.call("getblockchaininfo")
    median_time = chain_info.get("mediantime") if isinstance(chain_info, dict) else None
    if not isinstance(median_time, int):
        err_msg = f"getblockchaininfo answered {chain_info!r}, no int mediantime"
        raise TypeError(err_msg)
    return bytes.fromhex(best_hash), height, median_time


def _mine_one(
    tip: bytes,
    height: int,
    min_time: int,
    script_pub_key: ScriptPubKey,
    extra_transactions: Sequence[Tx] = (),
) -> tuple[Block, int]:
    """Build, solve and return one block extending `tip`, and its own time.

    Shared by `MiniWallet.generate` and `build_fork`: both mine a block
    through the same client-side path -- `build_coinbase` and
    `build_block` (`btclib.block.build`), then `mine`
    (`btclib.block.mining`) -- differing in what becomes of the result
    afterwards, submitted and cached by one and held for later submission
    by the other, and in whether anything beyond the coinbase rides along.

    :param tip: the previous block's own header hash.
    :param height: this block's own height.
    :param min_time: this block's own time must exceed this -- the
        previous block's own time, or the chain's median-time-past for
        the first block of a run.
    :param script_pub_key: what this block's coinbase pays.
    :param extra_transactions: already-broadcast transactions to carry
        along, in the order given -- a caller's own to have ordered so
        that a spend of one of them sits after it, since this class reads
        no mempool back to order them itself. `MiniWallet.generate`'s own
        `confirm` is the caller-facing name for this.
    :returns: the solved block, and the time it carries.
    :raises RuntimeError: `mine` exhausted its own search bound without
        solving one -- regtest's own target is wide enough that this is
        not expected to happen.
    """
    coinbase = build_coinbase(
        height, script_pub_key, halving_interval=_REGTEST_SUBSIDY_HALVING_INTERVAL
    )
    block_time = max(int(datetime.now(UTC).timestamp()), min_time + 1)
    candidate = build_block(
        tip,
        [coinbase, *extra_transactions],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(candidate.header)
    if solved is None:
        err_msg = f"no nonce solved height {height} within the search bound"
        raise RuntimeError(err_msg)
    return Block(solved, candidate.transactions, check_validity=False), block_time


def build_fork(
    node: NodeAdapter, script_pub_key: ScriptPubKey, length: int
) -> list[Block]:
    """Return `length` unsubmitted blocks extending `node`'s own current tip.

    `create_empty_fork`
    (`test/functional/test_framework/blocktools.py`): each block pays
    `script_pub_key` and carries no other transaction, mined client-side
    the same way `MiniWallet.generate` mines one, and none of them is
    submitted -- the caller does that, in order, once it wants to test
    what happens when this fork turns out to carry more work than
    whatever the node accepted in the meantime.

    Independent of any `MiniWallet` instance's own cache: a fork built
    this way is spent by nobody, so nothing here needs one.

    :param node: the node whose own current tip this fork extends.
    :param script_pub_key: what every block of the fork pays.
    :param length: how many blocks to build.
    :raises RuntimeError: `_mine_one` could not solve one of them.
    :raises TypeError: `node`'s own RPC answered something `_read_tip`
        cannot use.
    """
    tip, height, median_time = _read_tip(node)
    last_time = median_time
    blocks = []
    for _ in range(length):
        height += 1
        block, last_time = _mine_one(tip, height, last_time, script_pub_key)
        blocks.append(block)
        tip = block.header.hash
    return blocks


def nulldata_script_pub_key(data: bytes) -> ScriptPubKey:
    """Return an `OP_RETURN` scriptPubKey carrying `data`, of any length.

    `CScript([OP_RETURN, data])` (`test_framework/script.py`), not
    `ScriptPubKey.nulldata`: that classmethod's own 80-byte refusal is
    the historical "standard" bound, which a `-datacarriersize` test asks
    a *node* about rather than a fact this library should enforce before
    the request ever leaves this process
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)).
    `check_validity=False`: `ScriptPubKey.assert_valid` runs no length
    check of its own on a nulldata script, so this only ever skips the
    network-name check `Script.__init__` would otherwise repeat.

    :param data: the payload to push after `OP_RETURN`; any length,
        including one `ScriptPubKey.nulldata` would refuse.
    """
    return ScriptPubKey(script_serialize(["OP_RETURN", data]), check_validity=False)


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
        # seeded from the existing chain's own median-time-past rather than
        # 0: a node this wallet did not mine into -- the session-scoped
        # `bitcoind_adapter` fixture hands more than one MiniWallet the same
        # node -- already has a tip whose median-time-past this wallet's
        # first block must exceed, `time-too-old` otherwise
        self._tip, self._height, self._last_time = _read_tip(node)

    def resync(self) -> None:
        """Re-read this wallet's own tip, height and median-time from the node.

        For a chain move this wallet did not itself make -- an
        `invalidateblock`, or a `build_fork` a caller has just submitted --
        so that the next `generate` extends the chain that is actually
        there instead of a tip this wallet last saw before it moved.
        `_utxos` is left untouched: this class has no `scantxoutset` to
        rebuild it from (this module's own docstring has why), so a coin
        the move spent or unspent again is the caller's own to reconcile,
        from whatever RPC told it the move happened.
        """
        self._tip, self._height, self._last_time = _read_tip(self._node)

    @property
    def script_pub_key(self) -> ScriptPubKey:
        """Return the anyone-can-spend script every coin of this wallet pays."""
        return _ANYONE_CAN_SPEND

    def get_balance(self) -> int:
        """Return the satoshi sum of every coin this wallet still holds."""
        return sum(utxo.value for utxo in self._utxos)

    def generate(self, count: int, *, confirm: Sequence[Tx] = ()) -> list[bytes]:
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
        :param confirm: already-broadcast transactions to carry in the
            first of the `count` blocks -- `send_self_transfer`'s own
            return value, typically. Bitcoind's own node-side mining pulls
            the whole mempool in on every block; this class reads no
            mempool back, so a caller names exactly what it wants
            confirmed, in an order where a spend of one of them already
            sits after it.
        :returns: the mined blocks' own header hashes, display order,
            oldest first.
        :raises RuntimeError: `mine` exhausted its own search bound
            without solving one -- regtest's own target is wide enough
            that this is not expected to happen.
        :raises TypeError: `submitblock` answered anything but
            acceptance (`None`).
        """
        hashes = []
        for index in range(count):
            height = self._height + 1
            extra_transactions = confirm if index == 0 else ()
            block, block_time = _mine_one(
                self._tip,
                height,
                self._last_time,
                _ANYONE_CAN_SPEND,
                extra_transactions,
            )
            answer = self._node.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
            if answer is not None:
                err_msg = f"submitblock refused height {height}: {answer!r}"
                raise TypeError(err_msg)
            self._utxos.append(
                Utxo(
                    outpoint=OutPoint(block.transactions[0].id, 0),
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

    def get_utxo(self, *, txid: str) -> Utxo:
        """Return and forget the cached coin `txid` paid, maturity aside.

        `get_utxo` (`wallet.py`): a caller naming a coin by its own txid is
        presumed to already know what it is, so this applies no maturity
        filter -- `mempool_spend_coinbase.py`'s own subject is what the
        *node* does when handed a spend of one that has not cleared
        `COINBASE_MATURITY` yet, not a check this class should make first.

        :param txid: the hex txid of the coin's own transaction.
        :raises LookupError: no cached coin's own outpoint names `txid`.
        """
        for index, utxo in enumerate(self._utxos):
            if utxo.outpoint.tx_id.hex() == txid:
                return self._utxos.pop(index)
        err_msg = f"no coin of this wallet was paid by txid {txid!r}"
        raise LookupError(err_msg)

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

    def create_self_transfer(self, *, utxo_to_spend: Utxo | None = None) -> Tx:
        """Return an unbroadcast tx spending one coin, paid to itself.

        `send_self_transfer` is the caller wanting it broadcast too.

        :param utxo_to_spend: the coin to spend, `get_utxo`'s own answer
            typically; the next automatically matured one where `None`,
            `_pop_mature_utxo`'s own maturity check applying only then --
            a caller naming one by hand, immature or not, gets exactly
            that one, `create_self_transfer` (`wallet.py`)'s own shape.
        :raises LookupError: `utxo_to_spend` is `None` and no coin of this
            wallet has matured yet.
        """
        utxo = utxo_to_spend if utxo_to_spend is not None else self._pop_mature_utxo()
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

    def send_self_transfer(self, *, utxo_to_spend: Utxo | None = None) -> Tx:
        """Create, broadcast and cache a self-transfer; return the sent tx.

        The new coin `create_self_transfer` already cached is spendable
        the moment this returns: unlike a coinbase, `_pop_mature_utxo`
        never holds a non-coinbase coin back.

        :param utxo_to_spend: forwarded to `create_self_transfer`.
        :raises LookupError: `utxo_to_spend` is `None` and no coin of this
            wallet has matured yet.
        :raises TypeError: `sendrawtransaction` answered something other
            than the sent tx's own id.
        """
        tx = self.create_self_transfer(utxo_to_spend=utxo_to_spend)
        tx_hex = tx.serialize(True, check_validity=False).hex()
        txid = self._node.rpc.call("sendrawtransaction", [tx_hex])
        if txid != tx.id.hex():
            err_msg = f"sendrawtransaction answered {txid!r}, not {tx.id.hex()!r}"
            raise TypeError(err_msg)
        return tx

    def send_to(self, script_pub_key: ScriptPubKey, value: int) -> Tx:
        """Spend one matured coin, broadcast, paying `script_pub_key` too.

        `send_to` (`wallet.py`): a second output pays `script_pub_key`,
        and the first keeps `FEE` sat back for the fee and returns the
        rest to this wallet as change -- the same fixed-fee shape
        `create_self_transfer` already uses, so the spent coin's own
        value beyond `value` and `FEE` is not simply burned as a fee the
        way it would be paying a single output alone.

        :param script_pub_key: what the new, second output pays.
        :param value: the new output's own satoshi value.
        :raises LookupError: no coin of this wallet has matured yet.
        :raises ValueError: the spent coin cannot cover `value` and this
            class's own `FEE` together.
        :raises TypeError: `sendrawtransaction` answered something other
            than the sent tx's own id.
        """
        utxo = self._pop_mature_utxo()
        if utxo.value < value + FEE:
            err_msg = (
                f"coin of {utxo.value} sat cannot cover {value} sat plus "
                f"this class's own {FEE}-sat fee"
            )
            raise ValueError(err_msg)
        change = utxo.value - value - FEE
        tx_in = TxIn(
            utxo.outpoint,
            script_sig=b"",
            sequence=0xFFFFFFFE,
            script_witness=_witness(),
        )
        tx = Tx(
            version=2,
            lock_time=0,
            vin=[tx_in],
            vout=[TxOut(change, _ANYONE_CAN_SPEND), TxOut(value, script_pub_key)],
        )
        self._utxos.append(
            Utxo(outpoint=OutPoint(tx.id, 0), value=change, height=0, coinbase=False)
        )
        tx_hex = tx.serialize(True, check_validity=False).hex()
        txid = self._node.rpc.call("sendrawtransaction", [tx_hex])
        if txid != tx.id.hex():
            err_msg = f"sendrawtransaction answered {txid!r}, not {tx.id.hex()!r}"
            raise TypeError(err_msg)
        return tx
