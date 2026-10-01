# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_private_broadcast_cap`, one body over either node.

Read from Core's `test/functional/p2p_private_broadcast_cap.py`
(`82a02a2a2208`, 2026-07-07): a node given `-privatebroadcast` queues at
most `MAX_TRANSACTIONS` transactions, refuses a further one with an RPC
error and leaves the queue as it was, frees a slot when
`abortprivatebroadcast` removes one, and takes an already queued
transaction again without error.

The node's `-proxy` and `-i2psam` name a port nothing listens at: the
`-i2psam` makes I2P reachable, which `-privatebroadcast` needs to start,
and no step reads what the node asks of either. No proxy runs.

The body asks for `Capability.PRIVATE_BROADCAST`, and for the capability
of every other option its node is given: `PROXY` for `-proxy` and
`I2P_SAM` for `-i2psam`; `MINE` for Core's `MiniWallet`. Core's
`-dnsseed=0`, a line of its `write_config`, is passed on the command
line. Every step of Core's file is kept in its order.

What differs from Core's file:

- Core's node starts on its harness's cached chain. Here the
  `MiniWallet` mines the 101 blocks Core's first step mines, and the
  parent goes into a block of the wallet's own, where Core's
  `generateblock` mines it.
- a build before the cap has none: its queue takes every submission.
  The body reads `sendrawtransaction`'s `help` for the sentence that
  says the queue is bounded, and asserts that the first submission past
  the cap is refused exactly where the sentence is there. A build with
  no cap must take every later submission too, and its queue holds each
  one, the aborted one excepted.

A known limit: the refusal's code is `-37` from bitcoin/bitcoin#35678
(`3f3e644beb`, 2026-07-08) and `-7` before it, back to
bitcoin/bitcoin#35406 (`4498fa5d5b`, 2026-07-07). The body asserts `-37`
alone, so it fails against a build between the two.

`p2p_private_broadcast_cap_bitcoind_test.py` and
`p2p_private_broadcast_cap_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_core_rpc import RpcError
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from btclib.tx import Tx

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = ["private_broadcast_queue_is_capped"]

# Core's constants, from its file
_MAX_TRANSACTIONS = 10_000
_OVER_CAP = 5

# the code and message of the refusal
_FULL_CODE = -37
_FULL = "Private broadcast queue is full"

# the sentence `sendrawtransaction`'s help gains with the cap
_BOUNDED = "The private broadcast queue is bounded"


def _raw(tx: Tx) -> str:
    """Return `tx`'s own hex, witness included, for `sendrawtransaction`."""
    return tx.serialize(True).hex()


def _refused_as_full(node: NodeAdapter, tx: Tx) -> bool:
    """Send `tx`, and say whether the queue refused it as full.

    Any other refusal is raised.
    """
    refusal: RpcError | None = None
    try:
        node.rpc.call("sendrawtransaction", [_raw(tx)])
    except RpcError as err:
        refusal = err
    if refusal is None:
        return False
    assert refusal.code == _FULL_CODE, refusal
    assert _FULL in str(refusal), refusal
    return True


def _queued(node: NodeAdapter) -> list[dict[str, str]]:
    """Return the queue `getprivatebroadcastinfo` lists."""
    transactions: list[dict[str, str]] = node.rpc.call("getprivatebroadcastinfo")[
        "transactions"
    ]
    return transactions


def private_broadcast_queue_is_capped(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its order.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    extra_args = [
        "-privatebroadcast=1",
        "-i2psam=127.0.0.1:1",
        "-proxy=127.0.0.1:1",
        "-dnsseed=0",
    ]
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(
        cls, executable, tmp_path / "node0", rpc_port, p2p_port, extra_args
    )
    for capability in (
        Capability.PRIVATE_BROADCAST,
        Capability.I2P_SAM,
        Capability.PROXY,
        Capability.MINE,
    ):
        require(capability, node.capabilities, skip_counts)
    try:
        node.start()
        _run(node)
    finally:
        node.stop()


def _run(node: NodeAdapter) -> None:
    """Core's `run_test` over the started `node`."""
    wallet = MiniWallet(node)
    # mature one coinbase to spend
    wallet.generate(COINBASE_MATURITY + 1)

    # a parent that fans out to `_MAX_TRANSACTIONS + _OVER_CAP` outputs, put
    # in a block, since `-privatebroadcast` bypasses the mempool
    parent = wallet.create_self_transfer_multi(
        utxos_to_spend=[wallet.get_utxo()],
        num_outputs=_MAX_TRANSACTIONS + _OVER_CAP,
        fee_per_output=500,
    )
    wallet.generate(1, confirm=[parent])

    children = [
        wallet.create_self_transfer(utxo_to_spend=utxo)
        for utxo in wallet.new_utxos(parent)
    ]
    assert len(children) == _MAX_TRANSACTIONS + _OVER_CAP

    # fill the queue to the cap: every distinct submission succeeds
    for child in children[:_MAX_TRANSACTIONS]:
        node.rpc.call("sendrawtransaction", [_raw(child)])

    listed = _queued(node)
    assert len(listed) == _MAX_TRANSACTIONS
    present = {t["wtxid"] for t in listed}
    for i, child in enumerate(children[:_MAX_TRANSACTIONS]):
        assert child.hash.hex() in present, f"tx index {i} should be in the queue"

    # further distinct submissions are refused, and the queue is left as it
    # was; a build with no cap takes them
    over = children[_MAX_TRANSACTIONS:]
    capped = _BOUNDED in node.rpc.call("help", ["sendrawtransaction"])
    for child in over:
        refused = _refused_as_full(node, child)
        assert refused == capped
    if capped:
        assert listed == _queued(node)
        expected = {child.hash.hex() for child in children[:_MAX_TRANSACTIONS]}
    else:
        expected = {child.hash.hex() for child in children}
        assert len(_queued(node)) == len(expected)

    # `abortprivatebroadcast` frees a slot for a new submission
    aborted = node.rpc.call("abortprivatebroadcast", [children[1].id.hex()])
    assert [t["wtxid"] for t in aborted["removed_transactions"]] == [
        children[1].hash.hex()
    ]
    expected.discard(children[1].hash.hex())
    present = {t["wtxid"] for t in _queued(node)}
    assert len(present) == len(expected)
    assert children[1].hash.hex() not in present, "aborted tx should be gone"

    # the first transaction the queue refused, now taken where it was full,
    # and already queued where it was not
    node.rpc.call("sendrawtransaction", [_raw(over[0])])
    expected.add(over[0].hash.hex())
    present = {t["wtxid"] for t in _queued(node)}
    assert len(present) == len(expected)
    assert over[0].hash.hex() in present, "the new tx should be queued"
    assert children[1].hash.hex() not in present, "aborted tx should not reappear"

    # an already queued transaction is a no-op, not an error, even where
    # the queue is full
    node.rpc.call("sendrawtransaction", [_raw(children[0])])
    present = {t["wtxid"] for t in _queued(node)}
    assert len(present) == len(expected)
    assert children[0].hash.hex() in present, "the re-submitted tx should stay queued"
