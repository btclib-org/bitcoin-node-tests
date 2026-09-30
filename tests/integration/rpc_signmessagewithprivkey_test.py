# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_signmessagewithprivkey`, one body over either node.

Read from Core's `test/functional/rpc_signmessagewithprivkey.py`
(`fa5f29774872`, 2025-12-16), a file needing no mechanism the adapter
lacks ([ISS 317](https://github.com/btclib-org/bitcoin-node-tests/issues/317)):
one clean-chain node signs a message with a private key the caller hands
it, over `signmessagewithprivkey`, and verifies that signature under the
key's P2PKH address, over `verifymessage`
(`Capability.SIGN_MESSAGE_WITH_PRIVKEY`); it refuses to verify under the
key's P2SH-P2WPKH and P2WPKH addresses, refuses either call given the
wrong number of arguments, and refuses a private key, an address or a
signature it cannot decode. Every assertion of Core's own is kept.

What differs from Core's file: Core asks the node for the key's three
addresses, over `deriveaddresses`; btclib derives them here, by `p2pkh`,
`p2wpkh_p2sh` and `p2wpkh`, so that the node is asked only the calls the
test is about. Core's assertion that the P2PKH address is the one it
names is kept, and holds btclib's derivation to it.

Every step is the same at `v31.1`, the release `bitcoind.py` pins, whose
copy of the file is the pin's.

`rpc_signmessagewithprivkey_bitcoind_test.py` and
`rpc_signmessagewithprivkey_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.b32 import p2wpkh
from btclib.b58 import p2pkh, p2wpkh_p2sh, prv_key_data_from_wif

from bitcoin_node_tests.capability import Capability, require
from tests.integration.wallet_signmessagewithaddress_test import refused

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["a_message_signed_with_a_private_key_verifies"]

_MESSAGE = "This is just a test message"

# Core's own key, the signature it expects of it over `_MESSAGE`, and the
# key's P2PKH address, copied from its file
_WIF = "cUeKHd5orzT3mz8P9pxyREHfsWtVfgsfDjiZZBcjUBAaGk1BTj7N"
_SIGNATURE = "INbVnW4e6PeRmsv2Qgu8NuopvrVjkcxob+sX8OcZG0SALhWybUjzMLPdAsXI46YZGb0KQTRii+wWIQzRpG/U+S0="
_P2PKH_ADDRESS = "mpLQjfK79b7CCV4VMJWEWAj5Mpx8Up5zxB"

# `src/rpc/protocol.h`: what either RPC answers a call with the wrong
# number of arguments, its own help text as the message; what
# `verifymessage` answers an address that is not P2PKH, or a signature
# that is not base64; and what `signmessagewithprivkey` answers a key,
# and `verifymessage` an address, it cannot decode
_RPC_MISC_ERROR = -1
_RPC_TYPE_ERROR = -3
_RPC_INVALID_ADDRESS_OR_KEY = -5


def a_message_signed_with_a_private_key_verifies(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.SIGN_MESSAGE_WITH_PRIVKEY, node.capabilities, skip_counts)
    rpc = node.rpc

    # signing with the private key
    signature = rpc.call("signmessagewithprivkey", [_WIF, _MESSAGE])
    assert signature == _SIGNATURE

    # verifying with the P2PKH address succeeds
    pub_key = prv_key_data_from_wif(_WIF, "regtest").pub
    addresses = (p2pkh(pub_key), p2wpkh_p2sh(pub_key), p2wpkh(pub_key))
    assert addresses[0] == _P2PKH_ADDRESS
    assert rpc.call("verifymessage", [addresses[0], signature, _MESSAGE]) is True

    # verifying with a non-P2PKH address is refused
    for non_p2pkh_address in addresses[1:]:
        refused(
            rpc,
            "verifymessage",
            [non_p2pkh_address, signature, _MESSAGE],
            _RPC_TYPE_ERROR,
            "Address does not refer to key",
        )

    # `signmessagewithprivkey` takes a key and a message, no fewer and no
    # more
    for num_params in (0, 1, 3, 4, 5):
        refused(
            rpc,
            "signmessagewithprivkey",
            ["dummy"] * num_params,
            _RPC_MISC_ERROR,
            "signmessagewithprivkey",
        )
    # `verifymessage` takes an address, a signature and a message, no
    # fewer and no more
    for num_params in (0, 1, 2, 4, 5):
        refused(
            rpc,
            "verifymessage",
            ["dummy"] * num_params,
            _RPC_MISC_ERROR,
            "verifymessage",
        )

    # a key or an address that does not decode
    refused(
        rpc,
        "signmessagewithprivkey",
        ["invalid_key", _MESSAGE],
        _RPC_INVALID_ADDRESS_OR_KEY,
        "Invalid private key",
    )
    refused(
        rpc,
        "verifymessage",
        ["invalid_addr", signature, _MESSAGE],
        _RPC_INVALID_ADDRESS_OR_KEY,
        "Invalid address",
    )
    # a signature that is not base64
    refused(
        rpc,
        "verifymessage",
        [_P2PKH_ADDRESS, "invalid_sig", _MESSAGE],
        _RPC_TYPE_ERROR,
        "Malformed base64 encoding",
    )
