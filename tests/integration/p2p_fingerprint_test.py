# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_fingerprint`, one body over either node.

Read from Core's `test/functional/p2p_fingerprint.py` (`fa16bc53d79c`,
2026-04-16), a file needing no mechanism the adapter lacks
([ISS 317](https://github.com/btclib-org/bitcoin-node-tests/issues/317)):
a node withholds a block that is not on its active chain, and its
header, once the block is a month or more older than its best header,
so that a peer cannot fingerprint it by the stale blocks it holds.

With the node's clock set sixty days back (`Capability.CLOCK`), the node
mines a chain (`Capability.MINE`), and a peer announces by their headers
a longer fork built with btclib from two blocks below the tip, sending
each block once the node asks for it. The node reorganises onto the fork.

- The stale tip of the chain it left is served, block and header alike,
  while its best header is as old as it.
- Once the clock is released and the node mines a block of the present,
  neither the stale block nor its header is served.
- A block of the active chain as old as the stale one is still served,
  block and header alike.

What differs from Core's file:

- Core's `P2PInterface` records what the node sends from its framework's
  network thread, asking for every block the node announces by `inv`;
  here `_Conn` does both on the test's own thread, a wait reading the
  connection until its condition holds;
- each block and header the node is asked for is waited for with the
  last one received forgotten first. Core's waits for the stale block,
  and for the active chain's old block and its header, read a
  `last_message` that a block fetched from the node's own announcement,
  or the same request made just before, may already satisfy;
- the node mines to an address of its adapter's own choosing rather than
  to Core's own `get_deterministic_priv_key`'s, the chain being all the
  run reads of it;
- each block is built with btclib in the shape of Core's own
  `create_block` and `create_coinbase` (`blocktools.py`), its coinbase
  paying `OP_TRUE`.

Every step is the same at `v31.1`, the release `bitcoind.py` pins: Core's
file there differs from the pinned revision only in handing each
`create_block` a coinbase of its own `create_coinbase` rather than a
height, to the same block times. At `v29.4` it also spells a block's hash
and the sending of a message in its framework's older names.

`p2p_fingerprint_bitcoind_test.py` and `p2p_fingerprint_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import secrets
import time
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import (
    BlockPayload,
    GetData,
    GetHeaders,
    Headers,
    Inv,
    Inventory,
    InventoryType,
    Ping,
    Pong,
)
from btclib.p2p.magic import magic_from_chain

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.peer import Peer
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib.p2p import Message, Payload

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["stale_blocks_are_withheld"]

type _Node = BitcoindAdapter | BtclibNodeAdapter

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"

# Core's own `create_block` default, `VERSIONBITS_LAST_OLD_BLOCK_VERSION`
_BLOCK_VERSION = 4

# Core's own default wait, `P2PInterface`'s and `wait_until`'s
_WAIT = 60.0

# the wait Core's file gives each block and header it expects served
_SERVED_WAIT = 3.0

# how far back Core's file sets the node's clock: sixty days
_CLOCK_BACK = 60 * 24 * 60 * 60


class _Conn:
    """Core's own `P2PInterface`, as much of it as the file reads.

    `Peer.wait_for` drops what it does not wait for, so every wait here
    reads the connection itself and hands each message to `_handle`
    first. What the node sent last of each command is
    `Peer.last_message`, Core's `last_message`.

    :param peer: the connection, its handshake done.
    """

    def __init__(self, peer: Peer) -> None:
        self.peer = peer

    def send(self, payload: Payload) -> None:
        """Core's own `send_without_ping`."""
        self.peer.send(payload, check_validity=False)

    def _handle(self, message: Message) -> None:
        """Core's `P2PInterface.on_inv` and `on_ping`."""
        if message.command == "ping":
            self.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            wanted = [
                item for item in items if item.type_code != InventoryType.UNDEFINED
            ]
            if wanted:
                self.send(GetData(wanted))

    def wait_until(
        self, predicate: Callable[[], bool], *, timeout: float = _WAIT
    ) -> None:
        """Core's own `P2PInterface.wait_until`: read until `predicate` holds.

        :raises ConnectionError: the node closed the connection.
        :raises TimeoutError: `predicate` still failed at the wait's end.
        """
        err_msg = "condition not met within the wait"
        deadline = time.monotonic() + scaled(timeout)
        while not predicate():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(err_msg)
            try:
                message = self.peer.receive(timeout=remaining)
            except TimeoutError:
                raise TimeoutError(err_msg) from None
            self._handle(message)

    def sync_with_ping(self) -> None:
        """`Peer.sync_with_ping`'s barrier, every message read handled."""
        nonce = secrets.randbelow(2**64 - 1) + 1
        self.send(Ping(0))
        self.send(Ping(nonce))
        self.wait_until(
            lambda: (
                "pong" in self.peer.last_message
                and Pong.parse(self.peer.last_message["pong"].payload).nonce == nonce
            )
        )

    def has(self, command: str) -> bool:
        """Whether `command` is in Core's own `last_message`."""
        return command in self.peer.last_message

    def clear(self, *commands: str) -> None:
        """Forget the last message of each of `commands`."""
        for command in commands:
            self.peer.last_message.pop(command, None)

    def send_block_request(self, block_hash: bytes) -> None:
        """Core's own `send_block_request`: a `getdata` of one block."""
        self.send(GetData([Inventory(InventoryType.MSG_BLOCK, block_hash)]))

    def send_header_request(self, block_hash: bytes) -> None:
        """Core's own `send_header_request`: a stop hash, no locator."""
        self.send(GetHeaders(locator=[], hash_stop=block_hash))

    def wait_for_block(self, block_hash: bytes) -> None:
        """Core's own `wait_for_block`: the last `block` is `block_hash`'s."""

        def _received() -> bool:
            if not self.has("block"):
                return False
            payload = self.peer.last_message["block"].payload
            block = BlockPayload.parse(payload, check_validity=False).block
            return block.header.hash == block_hash

        self.wait_until(_received, timeout=_SERVED_WAIT)

    def wait_for_header(self, block_hash: bytes) -> None:
        """Core's own `wait_for_header`: the last `headers` opens with it."""

        def _received() -> bool:
            if not self.has("headers"):
                return False
            payload = self.peer.last_message["headers"].payload
            headers = Headers.parse(payload, check_validity=False).headers
            return bool(headers) and headers[0].hash == block_hash

        self.wait_until(_received, timeout=_SERVED_WAIT)

    def wait_for_getdata(self, hash_list: Sequence[bytes]) -> None:
        """Core's own `wait_for_getdata`: the last `getdata` is `hash_list`."""

        def _asked() -> bool:
            if not self.has("getdata"):
                return False
            items = GetData.parse(self.peer.last_message["getdata"].payload).items
            return [item.hash for item in items] == list(hash_list)

        self.wait_until(_asked)

    def block_is_served(self, block_hash: bytes) -> None:
        """Ask for the block, and wait for it, the last one forgotten first."""
        self.clear("block")
        self.send_block_request(block_hash)
        self.wait_for_block(block_hash)

    def header_is_served(self, block_hash: bytes) -> None:
        """Ask for the header, and wait for it, the last one forgotten first."""
        self.clear("headers")
        self.send_header_request(block_hash)
        self.wait_for_header(block_hash)


def _connect(stack: ExitStack, node: NodeAdapter) -> _Conn:
    """Core's own `add_p2p_connection(P2PInterface())`."""
    peer = stack.enter_context(Peer(node.p2p_address, _MAGIC))
    peer.handshake()
    conn = _Conn(peer)
    conn.sync_with_ping()
    return conn


def _block(previous: bytes, height: int, block_time: int) -> Block:
    """Core's own `create_block(previous, height=, ntime=)`, solved."""
    coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
    candidate = build_block(
        previous,
        [coinbase],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
        version=_BLOCK_VERSION,
    )
    solved = mine(candidate.header)
    assert solved is not None
    return Block(solved, candidate.transactions, check_validity=False)


def _build_chain(
    nblocks: int, prev_hash: bytes, prev_height: int, prev_median_time: int
) -> list[Block]:
    """Core's own `build_chain`: `nblocks` blocks on top of `prev_hash`."""
    blocks = []
    for _ in range(nblocks):
        block = _block(prev_hash, prev_height + 1, prev_median_time + 1)
        blocks.append(block)
        prev_hash = block.header.hash
        prev_height += 1
        prev_median_time += 1
    return blocks


def _count(node: NodeAdapter) -> int:
    """Return `getblockcount`'s own answer."""
    count = node.rpc.call("getblockcount")
    assert isinstance(count, int)
    return count


def _median_time(node: NodeAdapter, block_hash: bytes) -> int:
    """Return the `mediantime` `getblockheader` answers for `block_hash`."""
    header = node.rpc.call("getblockheader", [block_hash.hex()])
    assert isinstance(header, dict)
    median_time = header["mediantime"]
    assert isinstance(median_time, int)
    return median_time


def _mine(node: _Node, count: int) -> list[bytes]:
    """Core's own `generatetoaddress`, over `Capability.MINE`."""
    return [bytes.fromhex(block_hash) for block_hash in node.mine(count)]


def stale_blocks_are_withheld(
    cluster: Callable[[int], Sequence[_Node]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`, in Core's own order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MINE, node.capabilities, skip_counts)
    require(Capability.CLOCK, node.capabilities, skip_counts)

    with ExitStack() as stack:
        node0 = _connect(stack, node)

        node.set_mock_time(int(time.time()) - _CLOCK_BACK)

        block_hashes = _mine(node, 10)

        # a longer chain from two blocks below the tip
        height = len(block_hashes) - 2
        block_hash = block_hashes[height - 1]
        block_time = _median_time(node, block_hash) + 1
        new_blocks = _build_chain(5, block_hash, height, block_time)

        # the reorganisation onto it, headers first
        node0.send(
            Headers([block.header for block in new_blocks], check_validity=False)
        )
        node0.wait_for_getdata([block.header.hash for block in new_blocks])
        for block in new_blocks:
            node0.send(BlockPayload(block, include_witness=True, check_validity=False))
            node0.sync_with_ping()
        assert _count(node) == 13

        stale_hash = block_hashes[-1]

        # the stale block and its header, as old as the best header
        node0.block_is_served(stale_hash)
        node0.header_is_served(stale_hash)

        # the active chain extended at the present, a month past the stale block
        node.set_mock_time(0)
        (block_hash,) = _mine(node, 1)
        assert _count(node) == 14
        node0.wait_for_block(block_hash)

        # the stale block withheld
        node0.clear("block")
        node0.send_block_request(stale_hash)
        node0.sync_with_ping()
        assert not node0.has("block")

        # and its header
        node0.clear("headers")
        node0.send_header_request(stale_hash)
        node0.sync_with_ping()
        assert not node0.has("headers")

        # an old block of the active chain, and its header, still served
        block_hash = block_hashes[2]
        node0.send_block_request(block_hash)
        node0.send_header_request(block_hash)
        node0.sync_with_ping()

        node0.block_is_served(block_hash)
        node0.header_is_served(block_hash)
