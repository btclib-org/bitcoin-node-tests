# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_createwalletdescriptor`, one body over either node.

Read from Core's `test/functional/wallet_createwalletdescriptor.py`
(`fa5f29774872`, 2025-12-16, the same file at the pinned `v31.1`):
`createwalletdescriptor` adds an active descriptor of the type it is
asked for over an HD key the wallet already holds, and refuses where it
is given no key and the wallet's active descriptors name none or
several, where the key it is given has no private half there or is no
xpub, where the descriptor it would add exists already, and where an
encrypted wallet is locked. Every assertion of Core's own is kept.

`Capability.NODE_WALLET` (`capability.py`) is asked for, of a fresh
node of the body's own, and nothing more: no step reads the chain, every
descriptor imported with a `now` timestamp. Core's harness creates
`default_wallet` before the test runs, and imports its deterministic
coinbase key into it; this creates the wallet of that name itself and
imports no key, no step reading a coin. Its HD key's xprv is what the
other wallets import, as in Core. Core's `descsum_create`
(`test_framework/descriptors.py`) is btclib's `descriptors.add_checksum`,
and Core's `WalletUnlock` (`test_framework/wallet_util.py`) is `_unlocked`
below. Core reaches each wallet through `get_wallet_rpc`, as this does
through `rpc.for_wallet`.

`wallet_createwalletdescriptor_bitcoind_test.py` and
`wallet_createwalletdescriptor_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from btclib.descriptors.descriptors import add_checksum

from bitcoin_node_tests.capability import Capability, require
from tests.integration.wallet_signmessagewithaddress_test import refused

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from bitcoin_core_rpc import BitcoinCoreRpcClient

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["createwalletdescriptor_derives_from_a_key_the_wallet_holds"]

# Core's harness's own `default_wallet_name` (`test_framework.py`)
_WALLET = "default_wallet"

# Core's `WalletUnlock.MAXIMUM_TIMEOUT` (`test_framework/wallet_util.py`)
_UNLOCK_TIMEOUT = 999000

# `src/rpc/protocol.h`: what `createwalletdescriptor` answers
_RPC_WALLET_ERROR = -4
_RPC_INVALID_ADDRESS_OR_KEY = -5
_RPC_WALLET_UNLOCK_NEEDED = -13

_AMBIGUOUS_KEY = (
    "Unable to determine which HD key to use from active descriptors. "
    "Please specify with 'hdkey'"
)


@contextmanager
def _unlocked(wallet: BitcoinCoreRpcClient, passphrase: str) -> Iterator[None]:
    """Core's own `WalletUnlock`: unlocked inside, locked again on leaving."""
    wallet.call("walletpassphrase", [passphrase, _UNLOCK_TIMEOUT])
    try:
        yield
    finally:
        wallet.call("walletlock")


def _hd_key(wallet: BitcoinCoreRpcClient) -> tuple[str, str]:
    """Return the xpub and the xprv of the wallet's own first HD key."""
    key = wallet.call("gethdkeys", {"private": True})[0]
    return key["xpub"], key["xprv"]


def _descriptors(wallet: BitcoinCoreRpcClient) -> set[tuple[str, bool, bool]]:
    """Return each private descriptor's own string, `active` and `internal`."""
    return {
        (d["desc"], d["active"], d["internal"])
        for d in wallet.call("listdescriptors", {"private": True})["descriptors"]
    }


def _import_active(wallet: BitcoinCoreRpcClient, descriptor: str) -> None:
    """Import `descriptor` as active, asserting the node took it."""
    result = wallet.call(
        "importdescriptors",
        [[{"desc": add_checksum(descriptor), "timestamp": "now", "active": True}]],
    )
    assert result[0]["success"] is True


def _basic(node: BitcoindAdapter | BtclibNodeAdapter) -> None:
    """Core's `test_basic`."""
    def_wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call("createwallet", {"wallet_name": "blank", "blank": True})
    wallet = node.rpc.for_wallet("blank")

    xpub, xprv = _hd_key(def_wallet)
    expected_descs = [
        d["desc"]
        for d in def_wallet.call("listdescriptors")["descriptors"]
        if d["desc"].startswith("wpkh(")
    ]

    refused(
        wallet,
        "createwalletdescriptor",
        ["bech32"],
        _RPC_INVALID_ADDRESS_OR_KEY,
        _AMBIGUOUS_KEY,
    )
    refused(
        wallet,
        "createwalletdescriptor",
        {"type": "bech32", "hdkey": xpub},
        _RPC_INVALID_ADDRESS_OR_KEY,
        f"Private key for {xpub} is not known",
    )

    # one active descriptor imported into the blank wallet
    _import_active(wallet, f"pkh({xprv}/44h/2h/0h/0/0/*)")
    assert len(wallet.call("listdescriptors")["descriptors"]) == 1
    assert len(wallet.call("gethdkeys")) == 1

    new_descs = wallet.call("createwalletdescriptor", ["bech32"])["descs"]
    assert len(new_descs) == 2
    assert len(wallet.call("gethdkeys")) == 1
    assert new_descs == expected_descs

    # the descriptor creation options
    for internal, branch in ((False, 0), (True, 1)):
        old_descs = _descriptors(wallet)
        wallet.call("createwalletdescriptor", {"type": "bech32m", "internal": internal})
        added = list(_descriptors(wallet) - old_descs)
        assert len(added) == 1
        assert len(wallet.call("gethdkeys")) == 1
        assert added[0][0] == add_checksum(f"tr({xprv}/86h/1h/0h/{branch}/*)")
        assert added[0][1] is True
        assert added[0][2] is internal


def _imported_other_keys(node: BitcoindAdapter | BtclibNodeAdapter) -> None:
    """Core's `test_imported_other_keys`."""
    def_wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call("createwallet", {"wallet_name": "multiple_keys"})
    wallet = node.rpc.for_wallet("multiple_keys")

    wallet_xpub = wallet.call("gethdkeys")[0]["xpub"]
    xpub, xprv = _hd_key(def_wallet)

    _import_active(wallet, f"wpkh({xprv}/0/0/*)")
    assert len(wallet.call("gethdkeys")) == 2

    refused(
        wallet,
        "createwalletdescriptor",
        ["bech32"],
        _RPC_INVALID_ADDRESS_OR_KEY,
        _AMBIGUOUS_KEY,
    )
    refused(
        wallet,
        "createwalletdescriptor",
        {"type": "bech32m", "hdkey": wallet_xpub},
        _RPC_WALLET_ERROR,
        "Descriptor already exists",
    )
    refused(
        wallet,
        "createwalletdescriptor",
        {"type": "bech32m", "hdkey": xprv},
        _RPC_INVALID_ADDRESS_OR_KEY,
        "Unable to parse HD key. Please provide a valid xpub",
    )

    # the tr() descriptor replaced by one over the other HD key
    wallet.call("createwalletdescriptor", {"type": "bech32m", "hdkey": xpub})


def _encrypted(node: BitcoindAdapter | BtclibNodeAdapter) -> None:
    """Core's `test_encrypted`."""
    def_wallet = node.rpc.for_wallet(_WALLET)
    node.rpc.call(
        "createwallet",
        {"wallet_name": "encrypted", "blank": True, "passphrase": "pass"},
    )
    wallet = node.rpc.for_wallet("encrypted")

    _, xprv = _hd_key(def_wallet)

    with _unlocked(wallet, "pass"):
        _import_active(wallet, f"wpkh({xprv}/0/0/*)")
    assert len(wallet.call("gethdkeys")) == 1

    refused(
        wallet,
        "createwalletdescriptor",
        {"type": "bech32m"},
        _RPC_WALLET_UNLOCK_NEEDED,
        "Error: Please enter the wallet passphrase with walletpassphrase first.",
    )

    with _unlocked(wallet, "pass"):
        wallet.call("createwalletdescriptor", {"type": "bech32m"})


def createwalletdescriptor_derives_from_a_key_the_wallet_holds(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": _WALLET})
    _basic(node)
    _imported_other_keys(node)
    _encrypted(node)
