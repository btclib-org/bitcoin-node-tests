# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_tx_privacy`, one body over either node.

Read from Core's `test/functional/p2p_tx_privacy.py` (`fa5f29774872`,
2025-12-16): a transaction is announced only to a peer that had
completed its version handshake when the node received it. An originator
peer sends the node one transaction while a spy peer holds its own
handshake open, the spy then completes it, and the originator sends a
second: the spy's only announcement is the second transaction, by its
wtxid. Every assertion Core's file makes is kept.

`MiniWallet` (`Capability.MINE`) builds both transactions, as in Core.
It needs mature coins, so it first mines one block past
`COINBASE_MATURITY`, which matures the two coins the transactions spend,
where Core's own node starts on a chain its framework already mined.

`Peer` stands in for Core's `P2PInterface`. The originator is connected
and synced with a ping, as `TestNode.add_p2p_connection` does. The spy
is Core's `P2PTxSpy` connected with `wait_for_verack=False`: it sends
its own `version`, answers the node's with BIP339's `wtxidrelay` as
`P2PTxSpy.on_version` does, and waits for the node's `verack` while
holding back its own, which it sends only once the node has processed
the first transaction.

That order is held by one wait Core's file does not make: the spy's
`verack` goes out only once `getrawmempool` names the first
transaction. Core relies on `send_and_ping` alone, its `pong` coming
after the node has processed the `tx` sent ahead of it. A node that
answers a `ping` early
([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410))
could otherwise take the `verack` first, and a node that dropped the
transaction would pass the check below with nothing withheld.

`_wait_for_inv_match` is `P2PTxSpy.wait_for_inv_match`: it collects
every item of every `inv` the spy receives, and returns once they are
exactly the second transaction's `MSG_WTX`. The collection only grows,
so any other first item, or any item beside that one, is a failure at
once rather than at the deadline. Neither Core nor this port moves the
node's clock: the node announces to an inbound peer on its own timer,
and the second transaction's announcement is that timer firing for the
spy after the node took the first one in.

`p2p_tx_privacy_bitcoind_test.py` and `p2p_tx_privacy_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

import secrets
import time
from contextlib import ExitStack, suppress
from typing import TYPE_CHECKING

from btclib.p2p import (
    Inv,
    InventoryType,
    Ping,
    Pong,
    ServiceFlags,
    TxPayload,
    Verack,
    Version,
    WtxidRelay,
)
from btclib.p2p.magic import magic_from_chain
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import wait_until
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "a_tx_is_announced_only_to_a_peer_past_its_handshake",
]

_MAGIC = magic_from_chain("regtest")

# `Peer.handshake`'s own default, and Core's `P2P_SERVICES` (`p2p.py`)
_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS

# Core's own `wait_until` default, in seconds
_INV_TIMEOUT = 60.0


def _wait_for_inv_match(spy: Peer, expected: tuple[InventoryType, bytes]) -> None:
    """Core's `P2PTxSpy.wait_for_inv_match`, answering a `ping` meanwhile.

    :param expected: the one `(type, hash)` every `inv` item received
        must amount to.
    :raises AssertionError: the items received are not, and can no
        longer become, exactly `expected`.
    :raises TimeoutError: no `inv` arrived within `_INV_TIMEOUT`, scaled.
    """
    all_invs: list[tuple[InventoryType | int, bytes]] = []
    deadline = time.monotonic() + scaled(_INV_TIMEOUT)
    while all_invs != [expected]:
        assert not all_invs, f"announced {all_invs!r}, never exactly {expected!r}"
        remaining = deadline - time.monotonic()
        message = None
        if remaining > 0:
            with suppress(TimeoutError):
                message = spy.receive(timeout=remaining)
        if message is None:
            err_msg = f"no inv within the wait, expecting {expected!r}"
            raise TimeoutError(err_msg)
        if message.command == "ping":
            spy.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            all_invs += [(item.type_code, item.hash) for item in items]


def a_tx_is_announced_only_to_a_peer_past_its_handshake(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + 1)

    with ExitStack() as stack:
        tx_originator = stack.enter_context(Peer(node.p2p_address, _MAGIC))
        tx_originator.handshake()
        tx_originator.sync_with_ping()

        # the spy's handshake, held open short of its own verack
        spy = stack.enter_context(Peer(node.p2p_address, _MAGIC))
        spy.send(Version(services=_SERVICES, nonce=secrets.randbelow(2**64)))
        spy.wait_for("version")
        spy.send(WtxidRelay())
        spy.wait_for("verack")

        # tx_originator sends tx1
        tx1 = wallet.create_self_transfer()
        tx_originator.send(TxPayload(tx1, include_witness=True))
        tx_originator.sync_with_ping()
        wait_until(lambda: tx1.id.hex() in node.rpc.call("getrawmempool"))

        # Spy sends the verack
        spy.send(Verack())
        spy.sync_with_ping()

        # tx_originator sends tx2
        tx2 = wallet.create_self_transfer()
        tx_originator.send(TxPayload(tx2, include_witness=True))
        tx_originator.sync_with_ping()

        # Spy should only get an inv for the second transaction as the first
        # one was received pre-verack with the spy
        _wait_for_inv_match(spy, (InventoryType.MSG_WTX, tx2.hash))
