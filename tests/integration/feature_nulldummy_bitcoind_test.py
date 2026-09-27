# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_nulldummy`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_nulldummy.py` (`fa5f29774872`,
2025-12-16), every step of it kept in its own order
([ISS 64](https://github.com/btclib-org/bitcoin-node-tests/issues/64)):
`-testactivationheight=segwit@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds segwit, and NULLDUMMY (BIP147) with it, inactive until a chosen
height, and each step spends a multisig output whose dummy element --
the extra stack item `OP_CHECKMULTISIG` pops beyond its signatures -- is
empty or is `OP_TRUE`, in a P2SH scriptSig or a P2SH-P2WSH witness.
Before activation the mempool refuses a non-empty dummy and a block
still carries it; from the configured height on both refuse it, and an
empty dummy is still accepted by both.

The multisig is 0-of-1 where Core's own is 1-of-1, so no spend here
carries a signature: `EvalScript` (`src/script/interpreter.cpp`) checks
the dummy against `SCRIPT_VERIFY_NULLDUMMY` after its signature loop,
whatever the required count, so the refusal is the same
`SCRIPT_ERR_SIG_NULLDUMMY` a signed spend meets. The script is
serialized directly: `ScriptPubKey.p2ms` refuses a required count of
zero.

The two coins spent first are coinbases paying the P2SH output directly,
where Core's own pay a P2PKH key `signrawtransactionwithkey` signs for,
and each block carrying a step's transactions is built client-side
(`btclib.block.build`, `btclib.block.mining.mine`) where Core's own
asks `getblocktemplate`. `MiniWallet`'s own coins are P2TR, spent
through a witness, and bitcoind refuses a block carrying a witness
before segwit activates (`unexpected-witness`), so no `MiniWallet` coin
funds a step mined before the configured height; `MiniWallet.generate`
only matures the two coinbases. Every spend pays the P2SH output, the
witness one's funding aside, where Core's own steps 4 and 5 pay
`getnewdestination`'s fresh addresses. Core's own `-addresstype=legacy`
is dropped: it sets the address type of a node wallet, and this file
uses none.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.curves.curve import secp256k1
from btclib.script.script import serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# Core's own height: two coinbases, COINBASE_MATURITY blocks maturing
# them, two blocks before activation and the first one after
_SEGWIT_HEIGHT = COINBASE_MATURITY + 5

_NULLDUMMY_TX_ERROR = (
    "mempool-script-verify-flag-failed (Dummy CHECKMULTISIG argument must be zero)"
)
_NULLDUMMY_BLK_ERROR = (
    "block-script-verify-flag-failed (Dummy CHECKMULTISIG argument must be zero)"
)

# RPC_VERIFY_REJECTED, `src/rpc/protocol.h`
_RPC_VERIFY_REJECTED = -26

# secp256k1's own generator, an arbitrary valid public key: a 0-of-1
# multisig checks no signature against it
_G_X, _G_Y = secp256k1.G
_PUBKEY = bytes([2 + _G_Y % 2]) + _G_X.to_bytes(32, "big")

_MULTISIG = serialize(["OP_0", _PUBKEY, "OP_1", "OP_CHECKMULTISIG"])
_P2SH = ScriptPubKey.p2sh(_MULTISIG, "regtest")
_P2WSH = ScriptPubKey.p2wsh(_MULTISIG, "regtest")
_P2SH_P2WSH = ScriptPubKey.p2sh(_P2WSH.script, "regtest")

# Core's own amounts, whole bitcoins of a 50-bitcoin coinbase
_COIN = 100_000_000


def _start_adapter(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-testactivationheight=segwit@{_SEGWIT_HEIGHT}",),
    )
    adapter.start()
    return adapter


def _submit_block(
    adapter: BitcoindAdapter, transactions: list[Tx], script_pub_key: ScriptPubKey
) -> tuple[str | None, Block]:
    """Build, solve and submit a block extending `adapter`'s own tip.

    Core's own `block_submit`: `build_block` adds the witness commitment
    where a transaction carries a witness, as Core's own
    `add_witness_commitment` does where it is asked to.

    :returns: `submitblock`'s own answer, and the block.
    """
    tip = adapter.rpc.call("getbestblockhash")
    height = adapter.rpc.call("getblockcount") + 1
    median_time = adapter.rpc.call("getblockchaininfo")["mediantime"]
    coinbase = build_coinbase(
        height,
        script_pub_key,
        halving_interval=CONSENSUS_PARAMS["regtest"].subsidy_halving_interval,
    )
    block_time = max(int(datetime.now(UTC).timestamp()), median_time + 1)
    candidate = build_block(
        bytes.fromhex(tip),
        [coinbase, *transactions],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(candidate.header)
    if solved is None:
        err_msg = f"no nonce solved height {height} within the search bound"
        raise RuntimeError(err_msg)
    block = Block(solved, candidate.transactions, check_validity=False)
    answer = adapter.rpc.call(
        "submitblock", [block.serialize(check_validity=False).hex()]
    )
    return answer, block


def _assert_block(
    adapter: BitcoindAdapter, transactions: list[Tx], *, accept: bool
) -> None:
    """Submit a block carrying `transactions`; assert it is `accept`-ed or not.

    Refused, the answer is NULLDUMMY's own and the tip has not moved.
    """
    old_tip = adapter.rpc.call("getbestblockhash")
    answer, block = _submit_block(adapter, transactions, _P2SH)
    if accept:
        assert answer is None
        assert adapter.rpc.call("getbestblockhash") == block.header.hash.hex()
    else:
        assert answer == _NULLDUMMY_BLK_ERROR
        assert adapter.rpc.call("getbestblockhash") == old_tip


def _send(adapter: BitcoindAdapter, tx: Tx) -> None:
    """Broadcast `tx`, `maxfeerate` 0 as Core's own file passes it."""
    txid = adapter.rpc.call(
        "sendrawtransaction", [tx.serialize(True, check_validity=False).hex(), 0]
    )
    assert txid == tx.id.hex()


def _assert_refused(adapter: BitcoindAdapter, tx: Tx) -> None:
    """Assert the mempool refuses `tx` for its dummy element alone."""
    with pytest.raises(RpcError, match=re.escape(_NULLDUMMY_TX_ERROR)) as refusal:
        _send(adapter, tx)
    assert refusal.value.code == _RPC_VERIFY_REJECTED


def _base_spend(
    prev_out: OutPoint,
    value: int,
    *,
    dummy: str = "OP_0",
    script_pub_key: ScriptPubKey = _P2SH,
) -> Tx:
    """Return a spend of a `_P2SH` coin, `dummy` its scriptSig's first push.

    `OP_TRUE` is Core's own `invalidate_nulldummy_tx`.
    """
    script_sig = serialize([dummy, _MULTISIG])
    tx_in = TxIn(prev_out, script_sig=script_sig, sequence=0xFFFFFFFF)
    tx_out = TxOut(value, script_pub_key)
    return Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out])


def _witness_spend(prev_out: OutPoint, value: int, *, dummy: bytes = b"") -> Tx:
    r"""Return a spend of a `_P2SH_P2WSH` coin, `dummy` its first witness item.

    `b"\x01"` is Core's own tampered `scriptWitness.stack[0]`.
    """
    tx_in = TxIn(
        prev_out,
        script_sig=serialize([_P2WSH.script]),
        sequence=0xFFFFFFFF,
        script_witness=Witness([dummy, _MULTISIG]),
    )
    return Tx(version=2, lock_time=0, vin=[tx_in], vout=[TxOut(value, _P2SH)])


def test_nulldummy_is_policy_before_activation_and_consensus_after(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Core's own steps, in its own order, on one chain."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        coinbases = []
        for _ in range(2):
            answer, block = _submit_block(adapter, [], _P2SH)
            assert answer is None
            coinbases.append(block.transactions[0])
        MiniWallet(adapter).generate(COINBASE_MATURITY)

        # 1: compliant base spends, and a spend funding the witness
        # multisig, are relayed and mined before activation
        test1txs = [_base_spend(OutPoint(coinbases[0].id, 0), 49 * _COIN)]
        _send(adapter, test1txs[0])
        test1txs.append(_base_spend(OutPoint(test1txs[0].id, 0), 48 * _COIN))
        _send(adapter, test1txs[1])
        funding = _base_spend(
            OutPoint(coinbases[1].id, 0), 49 * _COIN, script_pub_key=_P2SH_P2WSH
        )
        test1txs.append(funding)
        _send(adapter, test1txs[2])
        _assert_block(adapter, test1txs, accept=True)

        # 2: a non-compliant base spend is refused by the mempool
        test2tx = _base_spend(OutPoint(test1txs[1].id, 0), 47 * _COIN, dummy="OP_TRUE")
        _assert_refused(adapter, test2tx)

        # 3: and still mined, the block before activation
        _assert_block(adapter, [test2tx], accept=True)

        # 4: from the configured height on, it is refused by both
        test4tx = _base_spend(OutPoint(test2tx.id, 0), 46 * _COIN, dummy="OP_TRUE")
        _assert_refused(adapter, test4tx)
        _assert_block(adapter, [test4tx], accept=False)

        # 5: and so is a non-compliant P2SH-P2WSH spend
        test5tx = _witness_spend(OutPoint(funding.id, 0), 48 * _COIN, dummy=b"\x01")
        _assert_refused(adapter, test5tx)
        _assert_block(adapter, [test5tx], accept=False)

        # 6: the same two spends with an empty dummy are relayed and mined
        test6txs = [
            _base_spend(OutPoint(test2tx.id, 0), 46 * _COIN),
            _witness_spend(OutPoint(funding.id, 0), 48 * _COIN),
        ]
        for tx in test6txs:
            _send(adapter, tx)
        _assert_block(adapter, test6txs, accept=True)
    finally:
        adapter.stop()
