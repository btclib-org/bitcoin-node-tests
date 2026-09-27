# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_sendmany`, one body over either node.

Read from Core's `test/functional/wallet_sendmany.py` (`fa5f29774872`,
2025-12-16, the same file at the pinned `v31.1`): `sendmany` refuses a
`subtractfeefrom` naming one output twice, an address it pays nothing,
a negative or an out-of-range position, or a value that is neither a
position nor an address, and takes one mixing an address with a
position. Every assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, then
`Capability.GENERATE`, the `generatetoaddress` the body funds the
sending wallet with, of a fresh node of the body's own on a clean chain,
as Core's `setup_clean_chain` asks. Core's harness creates
`default_wallet` before the test runs and imports its deterministic
coinbase key into it, and Core's `generate` mines to that key's
address, so the coins `sendmany` spends are that wallet's. This creates
the wallet of that name itself and mines the same blocks to an address
of its own instead. Core reaches both wallets through `get_wallet_rpc`,
as this does through `rpc.for_wallet`.

`wallet_sendmany_bitcoind_test.py` and `wallet_sendmany_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from tests.integration.wallet_signmessagewithaddress_test import refused

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["sendmany_refuses_a_subtractfeefrom_naming_no_single_output"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

# `src/rpc/protocol.h`: what `sendmany` answers a malformed argument
_RPC_INVALID_PARAMETER = -8

_SFFO = "Invalid parameter 'subtract fee from output'"


def sendmany_refuses_a_subtractfeefrom_naming_no_single_output(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test` and its `test_sffo_repeated_address`, in order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    node.rpc.call("createwallet", {"wallet_name": "activewallet"})
    wallet = node.rpc.for_wallet("activewallet")
    def_wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call("generatetoaddress", [101, def_wallet.call("getnewaddress")])

    addr_1 = wallet.call("getnewaddress")
    addr_2 = wallet.call("getnewaddress")
    addr_3 = wallet.call("getnewaddress")
    amounts = {addr_1: 1, addr_2: 1}

    for subtractfeefrom, message in (
        ([addr_1, addr_1, addr_1], f"{_SFFO}, duplicated position: 0"),
        ([addr_3], f"{_SFFO}, destination {addr_3} not found in tx outputs"),
        ([-5], f"{_SFFO}, negative position: -5"),
        ([5], f"{_SFFO}, position too large: 5"),
        ([False], f"{_SFFO}, invalid value type: bool"),
        ([0, addr_1], f"{_SFFO}, duplicated position: 0"),
    ):
        refused(
            def_wallet,
            "sendmany",
            {"dummy": "", "amounts": amounts, "subtractfeefrom": subtractfeefrom},
            _RPC_INVALID_PARAMETER,
            message,
        )

    # a string destination and a numeric index, mixed without a duplicate
    def_wallet.call(
        "sendmany", {"dummy": "", "amounts": amounts, "subtractfeefrom": [0, addr_2]}
    )
