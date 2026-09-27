# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_datacarrier`, one body per test over either node.

Read from Core's `test/functional/mempool_datacarrier.py` (`fa5f29774872`,
2025-12-16) and narrowed to what the option and MiniWallet families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-datacarrier` and `-datacarriersize` (`Capability.DATACARRIER`) gate
whether, and how large, an `OP_RETURN` output is relayed, and
`MiniWallet.create_self_transfer` (`Capability.MINE`) is what funds the
transaction that carries one, `mini_wallet.py`'s own
`nulldata_script_pub_key` building the output itself -- unlike
`ScriptPubKey.nulldata`, refusing no length, since a size limit is
exactly what a node's own `-datacarriersize` is being asked about here.

A smaller claim than Core's own file: kept are the default (uncapped)
setting, `-datacarrier=0` (no relay of any nulldata output, whatever its
size), a custom `-datacarriersize` at its own boundary, and the default
`permitbaremultisig` that `getmempoolinfo` reports, which Core's own file
checks here "rather than create a new test for it"; dropped is
Core's own fourth node (`-datacarriersize=2`) and its own full sweep of
`None`/zero-byte/one-byte payloads across every node, none of which
exercises a boundary the first three configurations do not already
cover.

Each body starts its node without the options it is about and restarts
it with them, where it names any, before any block is mined.

`mempool_datacarrier_bitcoind_test.py` and
`mempool_datacarrier_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx import TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, nulldata_script_pub_key

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "bare_multisig_is_permitted_by_default",
    "datacarrier_disabled_refuses_any_null_data_output",
    "datacarriersize_bounds_the_payload",
    "default_settings_allow_a_large_op_return",
]

# Core's own historical default -datacarriersize, "now used to test
# coverage" (its own file's comment) rather than any longer the default
_CUSTOM_DATACARRIER_SIZE = 83


def default_settings_allow_a_large_op_return(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check that with no `-datacarrier*` argument, a sizeable payload relays.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DATACARRIER, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    tx = wallet.create_self_transfer()
    tx.vout.append(TxOut(0, nulldata_script_pub_key(b"\xaa" * 500)))
    node.rpc.call(
        "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
    )
    assert tx.id.hex() in node.rpc.call("getrawmempool")


def datacarrier_disabled_refuses_any_null_data_output(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-datacarrier=0` refuses relay of a null-data output of any size.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DATACARRIER, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-datacarrier=0"])
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    tx = wallet.create_self_transfer()
    tx.vout.append(TxOut(0, nulldata_script_pub_key(b"")))
    with pytest.raises(RpcError, match="datacarrier"):
        node.rpc.call(
            "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
        )


def datacarriersize_bounds_the_payload(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a payload at the configured size relays; one byte more is refused.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.DATACARRIER, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-datacarrier=1", f"-datacarriersize={_CUSTOM_DATACARRIER_SIZE}"])
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)
    assert (
        node.rpc.call("getmempoolinfo")["maxdatacarriersize"]
        == _CUSTOM_DATACARRIER_SIZE
    )

    # OP_RETURN (1) + one-byte pushdata length (2) + data
    at_limit = wallet.create_self_transfer()
    at_limit.vout.append(
        TxOut(0, nulldata_script_pub_key(b"\xbb" * (_CUSTOM_DATACARRIER_SIZE - 3)))
    )
    node.rpc.call(
        "sendrawtransaction",
        [at_limit.serialize(True, check_validity=False).hex()],
    )
    assert at_limit.id.hex() in node.rpc.call("getrawmempool")

    over_limit = wallet.create_self_transfer()
    over_limit.vout.append(
        TxOut(0, nulldata_script_pub_key(b"\xbb" * (_CUSTOM_DATACARRIER_SIZE - 2)))
    )
    with pytest.raises(RpcError, match="datacarrier"):
        node.rpc.call(
            "sendrawtransaction",
            [over_limit.serialize(True, check_validity=False).hex()],
        )


def bare_multisig_is_permitted_by_default(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check that with no `-permitbaremultisig`, `getmempoolinfo` permits it.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PERMIT_BARE_MULTISIG, node.capabilities, skip_counts)
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    assert info["permitbaremultisig"] is True
