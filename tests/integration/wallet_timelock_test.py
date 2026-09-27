# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_timelock`, one body over either node.

Read from Core's `test/functional/wallet_timelock.py` (`fa5f29774872`,
2025-12-16, the same file at the pinned `v31.1`): a transaction whose
`nLockTime` is one second before the tip's median time past, once
confirmed, keeps its place in every balance and every list the wallet
answers after the node's clock is set back to that same second. Every
assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.GENERATE`, the `generatetoaddress` the body mines with, and
`Capability.CLOCK`, the `setmocktime` that sets the clock back, of a
fresh node of the body's own. Core runs on its harness's cached chain,
some of whose blocks pay the deterministic key its harness imports
into `default_wallet`, and mines to that key's address; this starts on
a clean chain, creates the wallet of that name itself, and mines to an
address of its own until a coinbase matures, before the test's own
first step. The tip's median time past is then the real clock's rather
than the cache's, and the clock is set back to one second before it
all the same: the transaction's `nLockTime` and the clock meet at the
same second either way. Core
reaches `default_wallet` over the node's own endpoint, it being the only
wallet loaded; this names it on every call, `BitcoindAdapter`'s own
docstring (`bitcoind.py`) having why.

`wallet_timelock_bitcoind_test.py` and `wallet_timelock_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["an_earlier_clock_leaves_a_confirmed_transaction_final"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

# Core's own label, a character outside ASCII in it
_LABEL = "timelock⌛🔓"


def _received(wallet: BitcoinCoreRpcClient, address: str) -> tuple[object, ...]:
    """Return every answer Core compares before and after the clock moves."""
    return (
        wallet.call("getreceivedbyaddress", [address]),
        wallet.call("getreceivedbylabel", [_LABEL]),
        wallet.call("listreceivedbyaddress", {"address_filter": address}),
        wallet.call("listreceivedbylabel", {"include_empty": False}),
        wallet.call("getbalances")["mine"]["trusted"],
        wallet.call("listunspent", {"maxconf": 1}),
    )


def an_earlier_clock_leaves_a_confirmed_transaction_final(
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
    require(Capability.CLOCK, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call("generatetoaddress", [101, wallet.call("getnewaddress")])

    tip = node.rpc.call("getbestblockhash")
    mtp_tip = node.rpc.call("getblockheader", [tip])["mediantime"]

    # a new address, with a label
    address = wallet.call("getnewaddress", {"label": _LABEL})

    # sent to with a locktime, and confirmed
    wallet.call("send", {"outputs": {address: 5}, "locktime": mtp_tip - 1})
    node.rpc.call("generatetoaddress", [1, wallet.call("getnewaddress")])

    # the clock cannot change the finality of a confirmed transaction
    before = _received(wallet, address)
    node.rpc.call("setmocktime", [mtp_tip - 1])
    after = _received(wallet, address)
    for was, now in zip(before, after, strict=True):
        assert now == was
