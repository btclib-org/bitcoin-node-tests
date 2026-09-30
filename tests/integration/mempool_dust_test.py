# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_dust`, one body per test over either node.

Read from Core's `test/functional/mempool_dust.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the option and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-permitbaremultisig` and `-dustrelayfee`
(`Capability.PERMIT_BARE_MULTISIG`, `Capability.DUST_RELAY_FEE`) are two
of the mempool's own relay-policy knobs, and `MiniWallet.create_self_transfer`
(`Capability.MINE`) funds the transaction whose extra output is measured
against them.

A smaller claim than Core's own file: kept is that a value clearly under the
dust threshold is refused and one clearly over it is allowed, for every output
shape Core's own list names that `ScriptPubKey` builds -- P2PK uncompressed and
compressed, P2PKH, P2SH, P2WPKH, P2WSH, P2TR and the largest standard bare
multisig -- and that `-dustrelayfee=0` waives the check entirely. Dropped is
Core's own file's exact per-byte threshold arithmetic (`GetDustThreshold`'s own
formula, reproduced by the test rather than read off the node), its
future-witness-version rows, `ScriptPubKey` having no generic
future-witness-version output of its own, its null data row, whose threshold is
zero and so sits on neither side of a boundary, and its full sweep of
`-dustrelayfee` values, none of which exercises a mechanism the coarser boundary
below does not already cover. Its ephemeral-dust two-transaction scenario is
dropped: ephemeral dust is its own acceptance rule
(`CheckEphemeralSpends`, `src/policy/ephemeral_policy.cpp`), exempting a dust
output its package spends, and the subject of Core's own
`mempool_ephemeral_dust.py`.

The public key every script below pays is secp256k1's own generator
point: none of these outputs is ever spent, only measured for its own
dust threshold, so no signature is needed and no key is generated for
it.

Each body starts its node without the options it is about and restarts
it with `-permitbaremultisig`, and `-dustrelayfee=0` where that is its
subject, before any block is mined.

`mempool_dust_bitcoind_test.py` and `mempool_dust_btclib_node_test.py`
run each body, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.curves.curve import secp256k1
from btclib.key import PubKeyData
from btclib.script.script_pub_key import ScriptPubKey
from btclib.tx import Tx, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_value_clearly_above_the_dust_threshold_is_allowed",
    "a_value_clearly_below_the_dust_threshold_is_refused",
    "dustrelayfee_zero_waives_the_dust_check",
]

# secp256k1's own generator, an arbitrary valid public key never spent
# below -- this module's own docstring is why one is never generated
_G_X, _G_Y = secp256k1.G
_ARBITRARY_PUBKEY = PubKeyData(bytes([2 + _G_Y % 2]) + _G_X.to_bytes(32, "big"))
_UNCOMPRESSED_PUBKEY = PubKeyData(
    b"\x04" + _G_X.to_bytes(32, "big") + _G_Y.to_bytes(32, "big")
)
_OP_TRUE = b"\x51"

# comfortably below and above any dust threshold this file's own
# -dustrelayfee values (the default, and 0) ever produce for the output
# shapes exercised here
_CLEARLY_DUST = 1
_CLEARLY_ABOVE_DUST = 100_000


def _output_scripts() -> tuple[tuple[ScriptPubKey, str], ...]:
    return (
        (ScriptPubKey.p2pk(_UNCOMPRESSED_PUBKEY), "P2PK (uncompressed)"),
        (ScriptPubKey.p2pk(_ARBITRARY_PUBKEY), "P2PK (compressed)"),
        (ScriptPubKey.p2pkh(_ARBITRARY_PUBKEY), "P2PKH"),
        (ScriptPubKey.p2sh(_OP_TRUE), "P2SH"),
        (ScriptPubKey.p2wpkh(_ARBITRARY_PUBKEY), "P2WPKH"),
        (ScriptPubKey.p2wsh(_OP_TRUE), "P2WSH"),
        (ScriptPubKey.p2tr(_ARBITRARY_PUBKEY), "P2TR"),
        (ScriptPubKey.p2ms(1, [_UNCOMPRESSED_PUBKEY] * 3), "bare multisig (1-of-3)"),
    )


def _tx_paying(wallet: MiniWallet, output_script: ScriptPubKey, value: int) -> Tx:
    """Return an unbroadcast self-transfer with one extra output, `value` sat.

    The wallet's own change output is reduced by `value`, so the second
    output's own value is what is actually measured against the dust
    threshold rather than added on top of it.
    """
    tx = wallet.create_self_transfer()
    tx.vout[0] = TxOut(tx.vout[0].value - value, tx.vout[0].script_pub_key)
    tx.vout.append(TxOut(value, output_script))
    return tx


def _mempool_accept(node: NodeAdapter, tx: Tx) -> dict[str, object]:
    """Return `testmempoolaccept`'s own result dict for `tx`, unfiltered."""
    tx_hex = tx.serialize(True, check_validity=False).hex()
    result: dict[str, object] = node.rpc.call("testmempoolaccept", [[tx_hex]])[0]
    return result


def _allowed(node: NodeAdapter, tx: Tx) -> bool:
    return bool(_mempool_accept(node, tx)["allowed"])


def a_value_clearly_below_the_dust_threshold_is_refused(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check every standard output shape refuses a one-satoshi value as dust.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PERMIT_BARE_MULTISIG, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-permitbaremultisig"])
    wallet = MiniWallet(node)
    # one matured coin per output shape below, each spent without a
    # further `generate` in between
    wallet.generate(COINBASE_MATURITY + len(_output_scripts()))
    for output_script, description in _output_scripts():
        tx = _tx_paying(wallet, output_script, _CLEARLY_DUST)
        result = _mempool_accept(node, tx)
        assert result["allowed"] is False, f"{description}: {result}"
        assert result["reject-reason"] == "dust", f"{description}: {result}"


def a_value_clearly_above_the_dust_threshold_is_allowed(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check every standard output shape allows a value well above dust.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PERMIT_BARE_MULTISIG, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-permitbaremultisig"])
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + len(_output_scripts()))
    for output_script, description in _output_scripts():
        tx = _tx_paying(wallet, output_script, _CLEARLY_ABOVE_DUST)
        assert _allowed(node, tx), f"{description} refused a value clearly above dust"


def dustrelayfee_zero_waives_the_dust_check(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-dustrelayfee=0` allows a value the default rate would refuse.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PERMIT_BARE_MULTISIG, node.capabilities, skip_counts)
    require(Capability.DUST_RELAY_FEE, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-permitbaremultisig", "-dustrelayfee=0"])
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    output_script, _ = _output_scripts()[0]
    tx = _tx_paying(wallet, output_script, _CLEARLY_DUST)
    assert _allowed(node, tx)
