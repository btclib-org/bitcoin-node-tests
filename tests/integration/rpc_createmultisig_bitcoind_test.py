# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_createmultisig`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/rpc_createmultisig.py` (`771200ca4362`,
2026-06-30) rather than ported whole: that file's own subject splits in
two, only one half of which this repository can demonstrate. Construction
-- `createmultisig` turning `(nsigs, pubkeys, output_type)` into an
address, a redeemScript and a descriptor -- needs no coin and no node
wallet, and is kept in full. Spending one -- `MiniWallet.send_to` funding
the multisig output, then `signrawtransactionwithkey` and
`combinerawtransaction` assembling real ECDSA signatures over it -- is a
claim about btclib's own signing surface, which every other module of
this suite already leaves to btclib's own test suite (rule 7 of issue
btclib-org/btclib#2220): `MiniWallet`'s own coins carry no signature at
all (`mini_wallet.py`'s own docstring), so a spend of a multisig output
built for real keys is not a claim this module's own mechanism can make.
Dropped for that reason: `do_multisig`'s own spend/sign/combine/broadcast
body, `test_combinerawtransaction_preconditions`,
`test_mixing_uncompressed_and_compressed_keys` (a claim about a spend's
own address fallback, the same reason).

Also dropped, and for a different reason: `test_multisig_script_limit`'s
own past-the-limit cases, and the "correct encoding" check past the same
bound. `ScriptPubKey.p2ms` (`btclib.script.script_pub_key`) refuses a
bare multisig script naming more keys than `OP_CHECKMULTISIG`'s own key
count can hold pushed as a small integer, `OP_16` being the largest one
a script has, by construction -- so there is no btclib construction to
compare bitcoind's own past-that-bound answer against; kept is the
"correct encoding" check up to `OP_16`'s own bound.
`test_sortedmulti_descriptors_bip67` is dropped for a third reason:
Core's own file reads its vectors from `data/rpc_bip67.json`, a vendored
fixture this repository does not carry.

No `Capability` and no `_btclib_node_test.py` counterpart: `createmultisig`
is not in `btclib_node`'s own dispatch table
(`src/btclib_node/rpc/callbacks.py`, measured at `main` `b853eb46`), the
same "bitcoind only" shape `feature_torcontrol.py`'s own row already
takes for a fact no other node under this repository's reach offers.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.descriptors import descriptors
from btclib.key import PrvKeyData
from btclib.script.script_pub_key import ScriptPubKey

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter

pytestmark = pytest.mark.integration

# deterministic, and never spent: construction is this module's whole
# subject, so a scalar in 1..n-1 is as good a key as a random one --
# `PrvKeyData(i, network="regtest").pub` is the SEC bytes `createmultisig`
# and btclib's own descriptor parser both take.
_KEYS = [PrvKeyData(i, network="regtest").pub.sec.hex() for i in range(1, 17)]

# Core's own `m_of_n` list (`rpc_createmultisig.py`), narrowed to what
# `ScriptPubKey.p2ms` can build: every entry already has n <= 15.
_M_OF_N = [(2, 3), (3, 3), (2, 5), (3, 5), (10, 15), (15, 15)]

_OUTPUT_TYPES = ("legacy", "p2sh-segwit", "bech32")


def _wrapped(nsigs: int, keys: list[str], output_type: str) -> str:
    """Return the unchecksummed descriptor `createmultisig` would report."""
    multi = f"multi({nsigs},{','.join(keys)})"
    if output_type == "legacy":
        return f"sh({multi})"
    if output_type == "p2sh-segwit":
        return f"sh(wsh({multi}))"
    return f"wsh({multi})"


def test_address_redeemscript_and_descriptor_match_btclibs_own_construction(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """Every `(nsigs, nkeys, output_type)` Core's own file names, matched."""
    for nsigs, nkeys in _M_OF_N:
        keys = _KEYS[:nkeys]
        expected_redeem_script = descriptors.parse(
            f"multi({nsigs},{','.join(keys)})", network="regtest"
        ).redeem_script()
        for output_type in _OUTPUT_TYPES:
            result = bitcoind_adapter.rpc.call(
                "createmultisig", [nsigs, keys, output_type]
            )
            descriptor = descriptors.parse(
                _wrapped(nsigs, keys, output_type), network="regtest"
            )
            assert result["redeemScript"] == expected_redeem_script.hex()
            assert result["address"] == descriptor.address()
            assert result["descriptor"] == descriptors.add_checksum(str(descriptor))


def test_encodes_every_key_count_up_to_the_bare_multisig_limit(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """`n`-of-`n`, for every `n` a bare `OP_CHECKMULTISIG` script can hold."""
    for nkeys in range(1, len(_KEYS) + 1):
        keys = [_KEYS[0]] * nkeys
        expected = ScriptPubKey.p2ms(
            nkeys,
            [PrvKeyData(1, network="regtest").pub] * nkeys,
            lexicographic_sorting=False,
        )
        result = bitcoind_adapter.rpc.call("createmultisig", [nkeys, keys, "bech32"])
        assert result["redeemScript"] == expected.script.hex()


def test_refuses_bech32m(bitcoind_adapter: BitcoindAdapter) -> None:
    """`bech32m` is refused: `createmultisig` has no witness v1 output."""
    with pytest.raises(
        RpcError, match="createmultisig cannot create bech32m multisig addresses"
    ):
        bitcoind_adapter.rpc.call("createmultisig", [2, _KEYS[:3], "bech32m"])
