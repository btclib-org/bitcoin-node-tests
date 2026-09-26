# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`fill_mempool`, driven against a faked RPC rather than a spawned node.

`mini_wallet_test.py`'s own doctrine applied here: `generate` runs the
real block construction and the real proof-of-work search, so only
`submitblock`, `sendrawtransaction`, `getnetworkinfo`, `getmempoolinfo`
and `getrawmempool` are faked, the calls this module's own `fill_mempool`
makes that touch a node for real. `getmempoolinfo` and `getrawmempool`
are scripted per test rather than modelling real eviction: each of
`fill_mempool`'s own `AssertionError` branches is reached by one
scripted answer, and one test takes the path where none of them fires.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, override

import pytest
from btclib.tx import Tx

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.mempool_util import fill_mempool
from bitcoin_node_tests.node import NodeAdapter

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from collections.abc import Set as AbstractSet

_GENESIS = "00" * 32

# a `relayfee`/`minrelaytxfee` comfortably matching bitcoind's own default
_RELAY_FEE = Decimal("0.00001")


def _txid_of(tx_hex: str) -> str:
    """Return the txid a serialized tx's own hex answers to on the wire.

    `mini_wallet_test.py`'s own helper of the same name: `Tx.parse` and
    `.id` are btclib's own, the same computation `send_self_transfer`
    (`mini_wallet.py`) checks `sendrawtransaction`'s own answer against.
    """
    return Tx.parse(BytesIO(bytes.fromhex(tx_hex))).id.hex()


class _FakeRpc:
    """A `bitcoin_core_rpc.BitcoinCoreRpcClient` stand-in: scripted answers.

    :param mempool_info_answers: what the first and the second
        `getmempoolinfo` call answer, in order -- `fill_mempool`'s own two
        calls, before and after the transactions meant to trigger
        eviction.
    :param raw_mempool: `getrawmempool`'s own answer, a function of every
        tx hex `sendrawtransaction` was sent so far -- so a test can name
        "the first transaction sent" (the low fee-rate one `fill_mempool`
        expects evicted) without knowing its txid up front.
    """

    def __init__(
        self,
        *,
        mempool_info_answers: Sequence[object],
        raw_mempool: Callable[[list[str]], list[str]] = lambda _sent: [],
        best_hash: str = _GENESIS,
        height: int = 0,
        median_time: int = 0,
    ) -> None:
        self._mempool_info_answers = list(mempool_info_answers)
        self._raw_mempool = raw_mempool
        self._best_hash = best_hash
        self._height = height
        self._median_time = median_time
        self.submitted: list[str] = []
        self.sent: list[str] = []

    def call(self, method: str, params: list[object] | None = None) -> object:
        tip_answers = {
            "getbestblockhash": self._best_hash,
            "getblockcount": self._height,
            "getblockchaininfo": {"mediantime": self._median_time},
        }
        if method in tip_answers:
            return tip_answers[method]
        if method == "submitblock":
            assert params is not None
            block_hex = params[0]
            assert isinstance(block_hex, str)
            self.submitted.append(block_hex)
            return None
        if method == "getnetworkinfo":
            return {"relayfee": _RELAY_FEE}
        if method == "getmempoolinfo":
            return self._mempool_info_answers.pop(0)
        if method == "getrawmempool":
            return self._raw_mempool(self.sent)
        assert method == "sendrawtransaction"
        assert params is not None
        tx_hex, maxfeerate = params
        assert isinstance(tx_hex, str)
        assert maxfeerate == 0
        self.sent.append(tx_hex)
        return _txid_of(tx_hex)


class _FakeNode(NodeAdapter):
    """A `NodeAdapter` answering `.rpc` with a `_FakeRpc`, never spawned."""

    capabilities: AbstractSet[Capability] = frozenset()

    def __init__(self, rpc: _FakeRpc) -> None:
        self._fake_rpc = rpc

    @override
    def _command(self) -> list[str]:
        return []

    @override
    def _rpc_client(self) -> _FakeRpc:  # type: ignore[override]
        return self._fake_rpc


def test_fake_node_is_never_actually_started() -> None:
    """`_command` exists to satisfy `NodeAdapter`, and answers nothing.

    `fill_mempool` never spawns a process, so nothing here ever calls
    `NodeAdapter.start`, the one caller `_command` otherwise has --
    `mini_wallet_test.py`'s own test of the same name is the same fact
    about the same `NodeAdapter` requirement.
    """
    node = _FakeNode(_FakeRpc(mempool_info_answers=[]))
    assert node._command() == []


def test_fill_mempool_evicts_the_lowest_fee_rate_transaction() -> None:
    """The path with none of the `AssertionError` checks tripped."""
    rpc = _FakeRpc(
        mempool_info_answers=[
            {"mempoolminfee": _RELAY_FEE},
            {"minrelaytxfee": _RELAY_FEE, "mempoolminfee": _RELAY_FEE * 2},
        ],
        raw_mempool=lambda _sent: [],
    )
    fill_mempool(_FakeNode(rpc))
    # the low fee-rate transaction, then 75 padded ones
    assert len(rpc.sent) == 76


def test_fill_mempool_refuses_eviction_starting_early() -> None:
    """`mempoolminfee` already above `relayfee` before the last 3 sends."""
    rpc = _FakeRpc(
        mempool_info_answers=[{"mempoolminfee": _RELAY_FEE * 2}],
        raw_mempool=lambda _sent: [],
    )
    with pytest.raises(AssertionError, match="already above"):
        fill_mempool(_FakeNode(rpc))


def test_fill_mempool_refuses_a_mempool_that_never_shrank() -> None:
    """Every transaction still in the mempool: nothing was evicted."""
    rpc = _FakeRpc(
        mempool_info_answers=[
            {"mempoolminfee": _RELAY_FEE},
            {"minrelaytxfee": _RELAY_FEE, "mempoolminfee": _RELAY_FEE * 2},
        ],
        raw_mempool=lambda sent: [_txid_of(tx_hex) for tx_hex in sent[1:]],
    )
    with pytest.raises(AssertionError, match="none evicted"):
        fill_mempool(_FakeNode(rpc))


def test_fill_mempool_refuses_the_low_fee_rate_tx_still_present() -> None:
    """The mempool shrank, but not of the transaction meant to be evicted."""
    rpc = _FakeRpc(
        mempool_info_answers=[
            {"mempoolminfee": _RELAY_FEE},
            {"minrelaytxfee": _RELAY_FEE, "mempoolminfee": _RELAY_FEE * 2},
        ],
        raw_mempool=lambda sent: [_txid_of(sent[0])],
    )
    with pytest.raises(AssertionError, match="was not evicted"):
        fill_mempool(_FakeNode(rpc))


def test_fill_mempool_refuses_minrelaytxfee_having_moved() -> None:
    """`minrelaytxfee` answering anything but `relayfee` is refused."""
    rpc = _FakeRpc(
        mempool_info_answers=[
            {"mempoolminfee": _RELAY_FEE},
            {"minrelaytxfee": _RELAY_FEE * 3, "mempoolminfee": _RELAY_FEE * 2},
        ],
        raw_mempool=lambda _sent: [],
    )
    with pytest.raises(AssertionError, match="moved off"):
        fill_mempool(_FakeNode(rpc))


def test_fill_mempool_refuses_mempoolminfee_not_having_risen() -> None:
    """`mempoolminfee` still at `relayfee` once every transaction is sent."""
    rpc = _FakeRpc(
        mempool_info_answers=[
            {"mempoolminfee": _RELAY_FEE},
            {"minrelaytxfee": _RELAY_FEE, "mempoolminfee": _RELAY_FEE},
        ],
        raw_mempool=lambda _sent: [],
    )
    with pytest.raises(AssertionError, match="did not rise above"):
        fill_mempool(_FakeNode(rpc))
