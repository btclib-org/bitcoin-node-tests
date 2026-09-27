# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_signmessagewithaddress`, one body over either node.

Read from Core's `test/functional/wallet_signmessagewithaddress.py`
(`fa5f29774872`, 2025-12-16, the same file at the pinned `v31.1`): one
clean-chain node under `-addresstype=legacy`, whose wallet signs a
message with an address of its own for the node to verify, whose
signature under one address does not verify under another, and which
refuses `signmessage` given the wrong number of arguments or an address
it cannot decode. Every assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for first, of a
fresh node of the body's own, which it restarts under
`-addresstype=legacy`: Core's `extra_args` start the node with the
option, and `bitcoind_cluster` (`tests/integration/conftest.py`) starts
one with none. Core's harness creates `default_wallet` before the test
runs, and imports its deterministic coinbase key into it; this creates
the wallet of that name itself and imports no key, no step reading a
coin. Core reaches that wallet over the node's own endpoint, it being
the only wallet loaded; this names it on every call, `BitcoindAdapter`'s
own docstring (`bitcoind.py`) having why.

`wallet_signmessagewithaddress_bitcoind_test.py` and
`wallet_signmessagewithaddress_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["refused", "signmessage_signs_for_the_address_it_names"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

_MESSAGE = "This is just a test message"

# `src/rpc/protocol.h`: what an `RPCHelpMan` answers a call with the
# wrong number of arguments, its own help text as the message, and what
# `signmessage` answers an address it cannot decode
_RPC_MISC_ERROR = -1
_RPC_INVALID_ADDRESS_OR_KEY = -5


def refused(
    client: BitcoinCoreRpcClient,
    method: str,
    params: Sequence[object] | Mapping[str, object],
    code: int,
    message: str,
) -> None:
    """Core's own `assert_raises_rpc_error`: `message` a substring, as there.

    `params` is positional or named, as `call`'s own. `message` is matched
    against the node's own message alone: `RpcError`'s text opens with the
    method and the endpoint (`bitcoin_core_rpc`'s own `_result`), so a
    `message` naming the method would match that prefix whatever the node
    answered.
    """
    with pytest.raises(RpcError) as excinfo:
        client.call(method, params)
    assert excinfo.value.code == code
    where = f"{method} at {client.url}: "
    assert excinfo.value.args[0].startswith(where)
    assert message in excinfo.value.args[0].removeprefix(where)


def signmessage_signs_for_the_address_it_names(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    node.restart(["-addresstype=legacy"])
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    wallet = node.rpc.for_wallet(_WALLET)

    # signing with an address of the wallet's own
    address = wallet.call("getnewaddress")
    signature = wallet.call("signmessage", [address, _MESSAGE])
    assert node.rpc.call("verifymessage", [address, signature, _MESSAGE]) is True

    # a signature does not verify under another address
    other_address = wallet.call("getnewaddress")
    other_signature = wallet.call("signmessage", [other_address, _MESSAGE])
    assert node.rpc.call("verifymessage", [other_address, signature, _MESSAGE]) is False
    assert node.rpc.call("verifymessage", [address, other_signature, _MESSAGE]) is False

    # `signmessage` takes an address and a message, no fewer and no more
    for num_params in (0, 1, 3, 4, 5):
        refused(
            wallet,
            "signmessage",
            ["dummy"] * num_params,
            _RPC_MISC_ERROR,
            "signmessage",
        )
    refused(
        wallet,
        "signmessage",
        ["invalid_addr", _MESSAGE],
        _RPC_INVALID_ADDRESS_OR_KEY,
        "Invalid address",
    )
