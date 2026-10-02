# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_sigoplimit`, one body over either node.

Read from Core's `test/functional/mempool_sigoplimit.py` (`5d25a0c28d19`,
2026-07-07) and narrowed to what the option and MiniWallet families
reach together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-bytespersigop` (`Capability.BYTES_PER_SIGOP`) converts a transaction's
own sigop count into an equivalent virtual size, and
`MiniWallet.send_to` funds a P2WSH output carrying a witness script this
file builds directly -- `OP_FALSE OP_IF <OP_CHECKSIG ...> OP_ENDIF
OP_TRUE`, Core's own `test_sigops_limit` construction: the branch
carrying the `OP_CHECKSIG`s is never executed (the script starts
`OP_FALSE OP_IF`), so no signature is ever needed, and the sigop count is
still charged -- legacy sigop counting is syntactic, not a trace of
execution.

A smaller claim than Core's own file: kept is `testmempoolaccept`'s own
`vsize` floor -- at the sigop-equivalent size, one byte above it, and
one byte below it, `max(sigop_equivalent_vsize, serialized_vsize)` in
each case, at one `-bytespersigop` and sigop count rather than Core's
own sweep across both. Dropped is Core's own file's ancestor and
descendant size accounting (`getmempoolentry`), its package-limit
scenario (`submitpackage`, cluster limits) and its legacy P2SH sigops
standardness test, all of which drive package or standardness mechanics
beyond a single transaction's own accepted vsize; none of them is
answered by the option and MiniWallet families alone.

The node starts without `-bytespersigop` and is restarted with it
before any block is mined, and with a `-datacarriersize` over the
`OP_RETURN` padding of the transactions below, which `v29.4` refuses by
default with `scriptpubkey` (`Capability.DATACARRIER`;
bitcoin/bitcoin#32406, first in `v30.0rc1`).

`mempool_sigoplimit_bitcoind_test.py` and
`mempool_sigoplimit_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING

from btclib.consensus import WITNESS_SCALE_FACTOR
from btclib.script.script import serialize
from btclib.script.script_pub_key import ScriptPubKey
from btclib.script.witness import Witness
from btclib.tx import OutPoint, Tx, TxIn, TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import (
    PADDING_DATACARRIER_SIZE,
    MiniWallet,
    nulldata_script_pub_key,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize"]

# a custom rate, standing in for Core's own default of 20: the option
# family's own subject is that the node honours whatever is configured,
# not this particular value
_BYTES_PER_SIGOP = 1000

_NUM_SIGOPS = 101
_FUNDING_VALUE = 1_000_000
_SPEND_VALUE = 500_000


def _witness_script(num_sigops: int) -> bytes:
    """Return a script whose own `OP_CHECKSIG`s are never executed.

    `OP_FALSE OP_IF ... OP_ENDIF OP_TRUE`: legacy sigop counting reads
    every opcode of a script regardless of which branch a run would
    actually take, so this carries `num_sigops` sigops and needs no
    signature to spend -- the script's own top-level branch is `OP_TRUE`.
    """
    return serialize(
        ["OP_FALSE", "OP_IF", *(["OP_CHECKSIG"] * num_sigops), "OP_ENDIF", "OP_TRUE"]
    )


def _spending_tx(funding_tx: Tx, witness_script: bytes, padding: bytes) -> Tx:
    tx_in = TxIn(
        OutPoint(funding_tx.id, 1),
        script_sig=b"",
        sequence=0xFFFFFFFE,
        script_witness=Witness([witness_script]),
    )
    tx_out = TxOut(_SPEND_VALUE, nulldata_script_pub_key(padding))
    return Tx(version=2, lock_time=0, vin=[tx_in], vout=[tx_out])


def a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `vsize` follows the sigop-equivalent floor, not the serialized one.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.BYTES_PER_SIGOP, node.capabilities, skip_counts)
    require(Capability.DATACARRIER, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(
        [
            f"-bytespersigop={_BYTES_PER_SIGOP}",
            f"-datacarriersize={PADDING_DATACARRIER_SIZE}",
        ]
    )
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    witness_script = _witness_script(_NUM_SIGOPS)
    funding_tx = wallet.send_to(ScriptPubKey.p2wsh(witness_script), _FUNDING_VALUE)
    node.rpc.call(
        "sendrawtransaction",
        [funding_tx.serialize(True, check_validity=False).hex()],
    )

    sigop_equivalent_vsize = ceil(_NUM_SIGOPS * _BYTES_PER_SIGOP / WITNESS_SCALE_FACTOR)
    # find the padding that makes the serialized vsize match the floor
    base_tx = _spending_tx(funding_tx, witness_script, b"")
    assert base_tx.vsize <= sigop_equivalent_vsize
    padding_len = 0
    while _spending_tx(funding_tx, witness_script, b"\x00" * padding_len).vsize < (
        sigop_equivalent_vsize
    ):
        padding_len += 1
    at_floor = _spending_tx(funding_tx, witness_script, b"\x00" * padding_len)
    assert at_floor.vsize == sigop_equivalent_vsize

    result = node.rpc.call(
        "testmempoolaccept",
        [[at_floor.serialize(True, check_validity=False).hex()]],
    )[0]
    assert result["allowed"], result
    assert result["vsize"] == sigop_equivalent_vsize

    above_floor = _spending_tx(funding_tx, witness_script, b"\x00" * (padding_len + 1))
    assert above_floor.vsize == sigop_equivalent_vsize + 1
    result = node.rpc.call(
        "testmempoolaccept",
        [[above_floor.serialize(True, check_validity=False).hex()]],
    )[0]
    assert result["allowed"], result
    assert result["vsize"] == sigop_equivalent_vsize + 1

    below_floor = _spending_tx(funding_tx, witness_script, b"\x00" * (padding_len - 1))
    assert below_floor.vsize < sigop_equivalent_vsize
    result = node.rpc.call(
        "testmempoolaccept",
        [[below_floor.serialize(True, check_validity=False).hex()]],
    )[0]
    assert result["allowed"], result
    # the sigop-equivalent floor wins over the smaller serialized size
    assert result["vsize"] == sigop_equivalent_vsize
