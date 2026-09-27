# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_coinbase_category`, one body over either node.

Read from Core's `test/functional/wallet_coinbase_category.py`
(`fa5f29774872`, 2025-12-16, the same file at the pinned `v31.1`): a
coinbase paying an address of the node's own wallet is `immature` in
`listtransactions`, `listsinceblock` and `gettransaction` until it
matures, `generate` once it has, and `orphan` once the block holding it
is invalidated. Every assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.GENERATE`, the `generatetoaddress` the body mines with, and
`Capability.INVALIDATE_BLOCK`, of a fresh node of the body's own on a
clean chain, as Core's `setup_clean_chain` asks.
Core's harness creates `default_wallet` before the test runs and imports
its deterministic coinbase key into it, and Core's `generate` mines to
that key's address: every coinbase the test mines is the wallet's own,
which is what `listtransactions`'s `skip` counts past. This creates the
wallet of that name itself and mines the blocks after the first to a
second address of its own instead, so `skip` counts the same
transactions. Core reaches that wallet over the node's own endpoint, it
being the only wallet loaded; this names it on every call,
`BitcoindAdapter`'s own docstring (`bitcoind.py`) having why.

`wallet_coinbase_category_bitcoind_test.py` and
`wallet_coinbase_category_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["a_coinbase_is_immature_then_generate_then_orphan"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"


def _assert_array_result(
    objects: Sequence[Mapping[str, object]],
    to_match: Mapping[str, object],
    expected: Mapping[str, object],
) -> None:
    """Core's own `assert_array_result` (`util.py`), `should_not_find` aside.

    Every object matching `to_match` carries `expected`, and at least one
    matches.
    """
    matched = [
        item for item in objects if all(item[k] == v for k, v in to_match.items())
    ]
    assert matched, f"No objects matched {to_match}"
    for item in matched:
        for key, value in expected.items():
            assert item[key] == value, f"{item} : expected {key}={value}"


def _assert_category(
    wallet: BitcoinCoreRpcClient,
    category: str,
    address: str,
    txid: str,
    skip: int,
) -> None:
    """Core's own `assert_category`: each wallet RPC agrees on `category`."""
    to_match = {"address": address}
    expected = {"category": category}
    _assert_array_result(
        wallet.call("listtransactions", {"skip": skip}), to_match, expected
    )
    _assert_array_result(
        wallet.call("listsinceblock")["transactions"], to_match, expected
    )
    _assert_array_result(
        wallet.call("gettransaction", [txid])["details"], to_match, expected
    )


def a_coinbase_is_immature_then_generate_then_orphan(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    require(Capability.INVALIDATE_BLOCK, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    wallet = node.rpc.for_wallet(_WALLET)

    # one block to an address
    address = wallet.call("getnewaddress")
    node.rpc.call("generatetoaddress", [1, address])
    block_hash = node.rpc.call("getbestblockhash")
    txid = node.rpc.call("getblock", [block_hash])["tx"][0]

    # immature after one confirmation
    _assert_category(wallet, "immature", address, txid, 0)

    # still immature at a depth of `COINBASE_MATURITY`
    other_address = wallet.call("getnewaddress")
    node.rpc.call("generatetoaddress", [99, other_address])
    _assert_category(wallet, "immature", address, txid, 99)

    # mature at the next block, so `generate`
    node.rpc.call("generatetoaddress", [1, other_address])
    _assert_category(wallet, "generate", address, txid, 100)

    # the block that paid the address invalidated, so `orphan`
    node.rpc.call("invalidateblock", [block_hash])
    _assert_category(wallet, "orphan", address, txid, 100)
