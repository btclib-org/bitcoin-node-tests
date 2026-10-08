# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_blank`, one body per `test_*` method over either node.

Read from Core's `test/functional/wallet_blank.py` (`fa5f29774872`,
2025-12-16, the same file at the pinned `v31.1`): a wallet created
blank keeps its `blank` flag once a descriptor is imported into it,
and once it is encrypted, its descriptors unchanged by the encryption.
Every assertion of Core's own is kept.

Each body asks `Capability.NODE_WALLET` (`capability.py`) of a fresh
node of its own, where Core runs both methods on one node started on
its cached chain: neither reads the chain, the descriptor
being imported with a `now` timestamp. Core's harness also creates
`default_wallet` on that node, which neither method reads; this creates
only the wallets each method names. Core's
`ADDRESS_BCRT1_UNSPENDABLE_DESCRIPTOR` (`test_framework/address.py`) is
btclib's: the regtest pay-to-witness-script-hash address of an
all-zero hash, checksummed by `descriptors.add_checksum`.

`wallet_blank_bitcoind_test.py` and `wallet_blank_btclib_node_test.py`
run them, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.b32 import address_from_witness
from btclib_wallet.descriptors.descriptors import add_checksum

from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "encryptwallet_keeps_the_blank_flag_and_the_descriptors",
    "importdescriptors_keeps_the_blank_flag",
]

# Core's `ADDRESS_BCRT1_UNSPENDABLE_DESCRIPTOR`
_UNSPENDABLE_DESCRIPTOR = add_checksum(
    f"addr({address_from_witness(0, bytes(32), 'regtest')})"
)


def importdescriptors_keeps_the_blank_flag(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `test_importdescriptors`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    node.rpc.call(
        "createwallet",
        {"wallet_name": "idesc", "disable_private_keys": True, "blank": True},
    )
    wallet = node.rpc.for_wallet("idesc")
    info = wallet.call("getwalletinfo")
    assert info["descriptors"] is True
    assert info["blank"] is True
    wallet.call(
        "importdescriptors", [[{"desc": _UNSPENDABLE_DESCRIPTOR, "timestamp": "now"}]]
    )
    assert wallet.call("getwalletinfo")["blank"] is True


def encryptwallet_keeps_the_blank_flag_and_the_descriptors(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `test_encrypt_descriptors`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.NODE_WALLET, node.capabilities, skip_counts)
    node.rpc.call("createwallet", {"wallet_name": "encblankdesc", "blank": True})
    wallet = node.rpc.for_wallet("encblankdesc")

    info = wallet.call("getwalletinfo")
    assert info["descriptors"] is True
    assert info["blank"] is True
    descs = wallet.call("listdescriptors")

    wallet.call("encryptwallet", ["pass"])
    assert wallet.call("getwalletinfo")["blank"] is True
    assert wallet.call("listdescriptors") == descs
