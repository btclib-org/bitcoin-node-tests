# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dersig`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_dersig.py` (`fab352053d6e`,
2026-04-16), on the option and MiniWallet families together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-testactivationheight=dersig@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds BIP66 inactive until a chosen height, and `MiniWallet.generate`
(`Capability.MINE`) mines to it with no node wallet.

Core's own closing checks are kept too, on a test of their own
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)):
a spend whose signature is not strict DER is mined in the block before
BIP66 activates, and from the configured height on is refused by
`testmempoolaccept` and `submitblock`, each in Core's own wording, while
the same spend DER-encoded is accepted. That needs a real ECDSA spend,
which `MiniWallet`'s own `ADDRESS_OP_TRUE` coins do not carry: its
coins are coinbases paying `RAW_P2PK_SCRIPT_PUB_KEY`, Core's own
`RAW_P2PK` output, spent under `raw_p2pk_script_sig` (`mini_wallet.py`),
at Core's own height so that they have matured. Dropped from it is the
debug-log wording of the block refusal, which `submitblock`'s own answer
already carries.

Kept, and read at the pinned bitcoind `31.1` rather than assumed:
`getdeploymentinfo`'s own `bip66` entry, which transitions from inactive
to active one block before the configured height -- the same "not
active as of current tip, but the next block must obey rules" boundary
Core's own file comments -- and the buried-deployment version floor
Core's own file also checks with a version-2 block once BIP66 is
active, `bad-version(0x00000002)` both in `submitblock`'s own answer and
in the node's own debug log (`ProcessNewBlock: AcceptBlock FAILED
(bad-version(0x00000002), ...)`, `src/validation.cpp`'s own
`ContextualCheckBlockHeader`). Not narrowed further than Core's own
file on this specific check: measured live against the pinned `31.1`,
a version-2 block is refused the same way both before and after BIP66's
own configured height, BIP65's own default floor (`-testactivationheight`
touching only the deployment it names) already requiring version 4 from
height 1 -- so Core's own file does not attempt the before/after
comparison for this check either, only the after-activation refusal.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.script.script import parse, serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import (
    FEE,
    RAW_P2PK_SCRIPT_PUB_KEY,
    MiniWallet,
    raw_p2pk_script_sig,
)
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# Core's own file hardcodes 102; this harness needs only that the height is
# reached in a handful of mined blocks, not that it matches Core's own value
_DERSIG_HEIGHT = 12

# Core's own height, which the signed spends below need: two coinbases
# paying `RAW_P2PK_SCRIPT_PUB_KEY` matured by the time the chain is two
# blocks short of it
_SIGNED_DERSIG_HEIGHT = COINBASE_MATURITY + 2


def _start_adapter(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    height: int = _DERSIG_HEIGHT,
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-testactivationheight=dersig@{height}",),
    )
    adapter.start()
    return adapter


def _block(
    adapter: BitcoindAdapter,
    script_pub_key: ScriptPubKey,
    *,
    version: int = 4,
    transactions: tuple[Tx, ...] = (),
) -> Block:
    """Return a solved, unsubmitted block extending `adapter`'s own tip.

    Built directly rather than through `MiniWallet.generate`: that method
    carries no `version` parameter, and its coinbase pays only the
    wallet's own script.

    :param adapter: the node whose own tip this block extends.
    :param script_pub_key: what the coinbase pays.
    :param version: the block header's own version; `4`, Core's own
        `create_block` default, where not given.
    :param transactions: what the block carries beside its coinbase.
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
        version=version,
    )
    solved = mine(candidate.header)
    if solved is None:
        err_msg = f"no nonce solved height {height} within the search bound"
        raise RuntimeError(err_msg)
    return Block(solved, candidate.transactions, check_validity=False)


def _submit(adapter: BitcoindAdapter, block: Block) -> object:
    """Return `submitblock`'s own answer for `block`."""
    return adapter.rpc.call(
        "submitblock", [block.serialize(check_validity=False).hex()]
    )


def _spend(coinbase: Tx, *, der: bool = True) -> Tx:
    """Return a signed spend of `coinbase`, a `RAW_P2PK_SCRIPT_PUB_KEY` coin.

    Where `der` is false the signature is Core's own `unDERify`'d one: a
    zero byte after S, ahead of the hash type, which BIP66's strict DER
    refuses and the lax parse before it does not.
    """
    tx_out = TxOut(coinbase.vout[0].value - FEE, RAW_P2PK_SCRIPT_PUB_KEY)
    unsigned = Tx(
        version=2, lock_time=0, vin=[TxIn(OutPoint(coinbase.id, 0))], vout=[tx_out]
    )
    script_sig = raw_p2pk_script_sig(unsigned, 0)
    if not der:
        (signature_hex,) = parse(script_sig)
        assert isinstance(signature_hex, str)  # `parse` answers a push as hex
        signature = bytes.fromhex(signature_hex)
        script_sig = serialize([signature[:-1] + b"\0" + signature[-1:]])
    tx_in = TxIn(OutPoint(coinbase.id, 0), script_sig=script_sig)
    return Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out])


def _bip66_active(adapter: BitcoindAdapter) -> bool:
    """Return `getdeploymentinfo`'s own `bip66` entry's `active`."""
    return (
        adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]["active"] is True
    )


def test_dersig_activates_one_block_before_the_configured_height(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """`getdeploymentinfo`'s own `bip66` entry tracks the configured height."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66 == {"type": "buried", "active": False, "height": _DERSIG_HEIGHT}

        wallet.generate(_DERSIG_HEIGHT - 2)
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66["active"] is False

        wallet.generate(1)  # tip is now one block before the configured height
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66["active"] is True
    finally:
        adapter.stop()


def test_a_block_below_the_minimum_version_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Once BIP66 is active, a version-2 block never becomes the tip."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_DERSIG_HEIGHT - 1)
        old_tip = adapter.rpc.call("getbestblockhash")

        block = _block(adapter, wallet.script_pub_key, version=2)
        answer = adapter.rpc.call(
            "submitblock", [block.serialize(check_validity=False).hex()]
        )

        assert answer == "bad-version(0x00000002)"
        assert adapter.rpc.call("getbestblockhash") == old_tip
    finally:
        adapter.stop()


def test_a_block_below_the_minimum_version_is_logged(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The same refusal, in bitcoind's own debug log wording."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_DERSIG_HEIGHT - 1)

        block = _block(adapter, wallet.script_pub_key, version=2)
        with assert_debug_log(adapter.debug_log_path, ["bad-version(0x00000002)"]):
            adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
    finally:
        adapter.stop()


def test_a_non_der_signature_is_refused_once_active(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A non-DER signature is mined before BIP66, and refused from it on."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(
        make_adapter, bitcoind_path, tmp_path, height=_SIGNED_DERSIG_HEIGHT
    )
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        coinbases = []
        for _ in range(2):
            block = _block(adapter, RAW_P2PK_SCRIPT_PUB_KEY)
            assert _submit(adapter, block) is None
            coinbases.append(block.transactions[0])
        MiniWallet(adapter).generate(_SIGNED_DERSIG_HEIGHT - 4)
        assert adapter.rpc.call("getblockcount") == _SIGNED_DERSIG_HEIGHT - 2
        assert not _bip66_active(adapter)

        # a non-DER signature can still appear in the block before activation
        block = _block(
            adapter,
            RAW_P2PK_SCRIPT_PUB_KEY,
            transactions=(_spend(coinbases[0], der=False),),
        )
        assert _submit(adapter, block) is None
        assert adapter.rpc.call("getbestblockhash") == block.header.hash.hex()
        assert _bip66_active(adapter)
        tip = block.header.hash.hex()

        # from the configured height on, the mempool refuses it for that alone
        spend = _spend(coinbases[1], der=False)
        txid = spend.id.hex()
        reason = "mempool-script-verify-flag-failed (Non-canonical DER signature)"
        details = (
            f"{reason}, input 0 of {txid} (wtxid {txid}), "
            f"spending {coinbases[1].id.hex()}:0"
        )
        answer = adapter.rpc.call(
            "testmempoolaccept",
            [[spend.serialize(False, check_validity=False).hex()], 0],
        )
        assert answer == [
            {
                "txid": txid,
                "wtxid": txid,
                "allowed": False,
                "reject-reason": reason,
                "reject-details": details,
            }
        ]

        # and so does a block
        block = _block(adapter, RAW_P2PK_SCRIPT_PUB_KEY, transactions=(spend,))
        answer = _submit(adapter, block)
        assert answer == "block-script-verify-flag-failed (Non-canonical DER signature)"
        assert adapter.rpc.call("getbestblockhash") == tip

        # while the same spend, DER-encoded, is accepted
        block = _block(
            adapter, RAW_P2PK_SCRIPT_PUB_KEY, transactions=(_spend(coinbases[1]),)
        )
        assert _submit(adapter, block) is None
        assert adapter.rpc.call("getbestblockhash") == block.header.hash.hex()
    finally:
        adapter.stop()
