# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`MiniWallet`, driven against a faked RPC rather than a spawned node.

`generate` runs the real block construction and the real proof-of-work
search (`build_coinbase`, `build_block`, `mine`): regtest's own target is
wide enough that a whole chain mines in well under a second, `node_test.py`'s
own `_FakeRpc` doctrine applied here to `submitblock` and
`sendrawtransaction`, the only two calls this module ever makes that
touch a node for real.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, override
from unittest.mock import patch

import pytest
from btclib.block.block import Block
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.mini_wallet import FEE, MiniWallet
from bitcoin_node_tests.node import NodeAdapter

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

_GENESIS = "00" * 32

# Core's own published address for the internal key 1 and a single OP_TRUE
# leaf (`test_framework/address.py`'s own
# `create_deterministic_address_bcrt1_p2tr_op_true`)
_ADDRESS_OP_TRUE = "bcrt1p9yfmy5h72durp7zrhlw9lf7jpwjgvwdg0jr0lqmmjtgg83266lqsekaqka"


class _FakeRpc:
    """A `bitcoin_core_rpc.BitcoinCoreRpcClient` stand-in: scripted answers.

    :param best_hash: what `getbestblockhash` answers.
    :param height: what `getblockcount` answers.
    :param median_time: what `getblockchaininfo`'s own `mediantime` answers
        -- a chain this wallet did not itself mine, the way the
        session-scoped `bitcoind_adapter` fixture hands more than one
        `MiniWallet` the same node, already has one.
    :param submit_answer: what every `submitblock` answers; `None` is
        acceptance, matching bitcoind's own convention.
    :param send_answer: what `sendrawtransaction` answers; a fixed value
        that overrides the sent tx's own id where given, so that
        `send_self_transfer`'s own mismatch check can be exercised.
    """

    def __init__(
        self,
        *,
        best_hash: str = _GENESIS,
        height: int = 0,
        median_time: int = 0,
        submit_answer: object = None,
        send_answer: object = "sentinel",
    ) -> None:
        self._best_hash = best_hash
        self._height = height
        self._median_time = median_time
        self._submit_answer = submit_answer
        self._send_answer = send_answer
        self.submitted: list[str] = []
        self.sent: list[str] = []

    def call(self, method: str, params: list[object] | None = None) -> object:
        if method == "getbestblockhash":
            return self._best_hash
        if method == "getblockcount":
            return self._height
        if method == "getblockchaininfo":
            return {"mediantime": self._median_time}
        if method == "submitblock":
            assert params is not None
            block_hex = params[0]
            assert isinstance(block_hex, str)
            self.submitted.append(block_hex)
            return self._submit_answer
        # the only call left this fake ever answers: sendrawtransaction
        assert method == "sendrawtransaction"
        assert params is not None
        tx_hex = params[0]
        assert isinstance(tx_hex, str)
        self.sent.append(tx_hex)
        if self._send_answer == "sentinel":
            return _txid_of(tx_hex)
        return self._send_answer


def _txid_of(tx_hex: str) -> str:
    """Return the txid a serialized tx's own hex answers to on the wire.

    `_FakeRpc.call` uses this so that its default `sendrawtransaction`
    answer is always right, without hard-coding one -- `Tx.parse` and
    `.id` are btclib's own, the same computation `send_self_transfer`
    checks its answer against.
    """
    from io import BytesIO  # noqa: PLC0415

    from btclib.tx import Tx  # noqa: PLC0415

    return Tx.parse(BytesIO(bytes.fromhex(tx_hex))).id.hex()


class _FakeNode(NodeAdapter):
    """A `NodeAdapter` answering `.rpc` with a `_FakeRpc`, never spawned.

    `node_test.py`'s own `_FakeAdapter`: `MiniWallet` reads nothing off a
    node but `.rpc`, so `_command` and `_rpc_client` below are never
    called by anything this module's own tests exercise.
    """

    capabilities: AbstractSet[Capability] = frozenset()

    def __init__(self, rpc: _FakeRpc) -> None:
        self._fake_rpc = rpc

    @override
    def _command(self) -> list[str]:
        return []

    @override
    def _rpc_client(self) -> _FakeRpc:  # type: ignore[override]
        return self._fake_rpc


def test_init_reads_the_current_tip_and_height() -> None:
    """The constructor asks for nothing but where the chain already is."""
    rpc = _FakeRpc(best_hash="ab" * 32, height=7)
    wallet = MiniWallet(_FakeNode(rpc))
    assert wallet.get_balance() == 0
    assert wallet.script_pub_key.address == _ADDRESS_OP_TRUE


def test_fake_node_is_never_actually_started() -> None:
    """`_command` exists to satisfy `NodeAdapter`, and answers nothing.

    `MiniWallet` never spawns a process, so nothing here ever calls
    `NodeAdapter.start`, the one caller `_command` otherwise has -- this
    is the whole of what covers it.
    """
    node = _FakeNode(_FakeRpc())
    assert node._command() == []


@pytest.mark.parametrize("best_hash", [123, None])
def test_init_refuses_a_non_string_best_hash(best_hash: object) -> None:
    """`getbestblockhash` answering anything but a string is refused."""
    rpc = _FakeRpc()
    with (
        patch.object(_FakeRpc, "call", return_value=best_hash),
        pytest.raises(TypeError, match="getbestblockhash"),
    ):
        MiniWallet(_FakeNode(rpc))


def test_init_refuses_a_non_int_height() -> None:
    """`getblockcount` answering anything but an int is refused."""
    rpc = _FakeRpc()
    calls = {"n": 0}

    def _call(
        _self: _FakeRpc, method: str, params: list[object] | None = None
    ) -> object:
        del params
        calls["n"] += 1
        if method == "getbestblockhash":
            return _GENESIS
        assert method == "getblockcount"
        return "not-an-int"

    with (
        patch.object(_FakeRpc, "call", _call),
        pytest.raises(TypeError, match="getblockcount"),
    ):
        MiniWallet(_FakeNode(rpc))


@pytest.mark.parametrize("chain_info", [123, None, {}, {"mediantime": "x"}])
def test_init_refuses_a_bad_getblockchaininfo_answer(chain_info: object) -> None:
    """`getblockchaininfo` answering no int `mediantime` is refused."""
    rpc = _FakeRpc()

    def _call(
        _self: _FakeRpc, method: str, params: list[object] | None = None
    ) -> object:
        del params
        if method == "getbestblockhash":
            return _GENESIS
        if method == "getblockcount":
            return 0
        assert method == "getblockchaininfo"
        return chain_info

    with (
        patch.object(_FakeRpc, "call", _call),
        pytest.raises(TypeError, match="getblockchaininfo"),
    ):
        MiniWallet(_FakeNode(rpc))


def test_generate_mines_and_caches_one_coin_per_block() -> None:
    """`generate` builds, mines and submits, with no RPC scan afterwards."""
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    hashes = wallet.generate(3)
    assert len(hashes) == 3
    assert len(rpc.submitted) == 3
    assert wallet.get_balance() > 0


def test_generate_halves_the_subsidy_at_regtest_s_own_interval() -> None:
    """Regtest halves at height 150, not at mainnet's 210000.

    A coinbase claiming mainnet's subsidy past that height is refused by
    bitcoind as `bad-cb-amount`; both the coinbase each block carries and
    the value this wallet caches for it must halve there.
    """
    rpc = _FakeRpc(height=148)
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(2)
    paid = [
        Block.parse(bytes.fromhex(block_hex), check_validity=False)
        .transactions[0]
        .vout[0]
        .value
        for block_hex in rpc.submitted
    ]
    assert paid == [5_000_000_000, 2_500_000_000]
    assert wallet.get_balance() == sum(paid)


def test_generate_seeds_the_first_block_time_from_the_chains_mediantime() -> None:
    """A wallet built on a pre-existing chain does not mine `time-too-old`.

    The session-scoped `bitcoind_adapter` fixture hands more than one
    `MiniWallet` the same node: a chain another wallet already mined many
    blocks into rapidly leaves a median-time-past ahead of the wall clock,
    which this wallet's own first block still has to exceed.
    """
    far_future_median_time = int(datetime.now(UTC).timestamp()) + 10_000
    rpc = _FakeRpc(median_time=far_future_median_time)
    wallet = MiniWallet(_FakeNode(rpc))

    wallet.generate(1)

    block = Block.parse(bytes.fromhex(rpc.submitted[0]), check_validity=False)
    assert int(block.header.time.timestamp()) > far_future_median_time


def test_generate_refuses_a_submitblock_rejection() -> None:
    """A `submitblock` answer other than acceptance is not swallowed."""
    rpc = _FakeRpc(submit_answer="bad-block-header")
    wallet = MiniWallet(_FakeNode(rpc))
    with pytest.raises(TypeError, match="submitblock refused"):
        wallet.generate(1)


def test_generate_refuses_an_unsolved_candidate() -> None:
    """A `mine` search that comes back empty is reported, not retried."""
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    with (
        patch("bitcoin_node_tests.mini_wallet.mine", return_value=None),
        pytest.raises(RuntimeError, match="no nonce solved"),
    ):
        wallet.generate(1)


def test_create_self_transfer_refuses_with_no_matured_coin() -> None:
    """A coin mined this call is not yet `COINBASE_MATURITY` deep."""
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(1)
    with pytest.raises(LookupError, match="no coin"):
        wallet.create_self_transfer()


def test_create_self_transfer_spends_a_matured_coin() -> None:
    """A coin `COINBASE_MATURITY` blocks deep is spendable."""
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(COINBASE_MATURITY + 1)
    balance_before = wallet.get_balance()

    tx = wallet.create_self_transfer()

    assert len(tx.vin) == 1
    assert len(tx.vout) == 1
    assert tx.vout[0].script_pub_key == wallet.script_pub_key
    assert wallet.get_balance() == balance_before - FEE


def test_create_self_transfer_can_spend_a_coin_it_already_created() -> None:
    """A non-coinbase coin this class itself minted needs no maturity wait.

    Exactly `COINBASE_MATURITY` blocks, not one more: mining a second
    matured coinbase alongside the first would let the second call below
    pop *that* one instead, `_pop_mature_utxo`'s own oldest-first order
    never reaching the coin `create_self_transfer` just minted.
    """
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(COINBASE_MATURITY)

    first = wallet.create_self_transfer()
    second = wallet.create_self_transfer()

    assert second.vin[0].prev_out.tx_id == first.id


def test_send_self_transfer_broadcasts_and_returns_the_sent_tx() -> None:
    """The tx sent is the one `create_self_transfer` built, byte for byte."""
    rpc = _FakeRpc()
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(COINBASE_MATURITY + 1)

    tx = wallet.send_self_transfer()

    assert len(rpc.sent) == 1
    assert rpc.sent[0] == tx.serialize(True, check_validity=False).hex()


def test_send_self_transfer_refuses_a_mismatched_answer() -> None:
    """An answer other than the sent tx's own id is refused, not trusted."""
    rpc = _FakeRpc(send_answer="not-the-txid")
    wallet = MiniWallet(_FakeNode(rpc))
    wallet.generate(COINBASE_MATURITY + 1)
    with pytest.raises(TypeError, match="sendrawtransaction answered"):
        wallet.send_self_transfer()
