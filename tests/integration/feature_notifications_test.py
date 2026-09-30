# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_notifications`, a body per option over either node.

Read from Core's `test/functional/feature_notifications.py`
(`469b0e59a29a`, 2026-09-01), the option and the disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)).
Each command Core's first node runs writes a file the test reads back,
and each is a body here, over a node of its own started with that
option alone:

- `-blocknotify` (`Capability.BLOCK_NOTIFY`): the node mines blocks
  (`Capability.MINE`), and its command writes one file per block, named
  for the block's hash;
- `-alertnotify` (`Capability.ALERT_NOTIFY`): the node takes the
  headers of a chain of blocks each paying its coinbase one satoshi more
  than the subsidy, over `submitheader`, then the blocks, tip first,
  over `submitblock` (`Capability.MINE`), and its command appends the
  warning about an invalid chain with more work than its own to a file,
  in the wording the runner says the running build raises;
- `-shutdownnotify` (`Capability.SHUTDOWN_NOTIFY`): the node's command
  writes a file once the node is stopped.

The blocks of the invalid chain are built with btclib in the shape of
Core's own `create_block`, each one second after the last, the first
extending the node's tip.

What differs from Core's file:

- `-walletnotify`, given to the file's second node, is not ported: it
  asks for a second node's own wallet sharing the first's descriptors,
  built from an extended private key the client generates, which
  `TF2.md`'s own *The node wallet* section lists among what a port of
  Core's wallet tests still waits on;
- Core's blocks are mined by the second node and notified by the first
  once they reach it; here the node given `-blocknotify` mines them;
- Core runs every check on one node, in turn, its invalid chain
  extending the chain its earlier checks mined; here each body starts a
  node of its own, and the alert's node mines as many blocks as the
  `-blocknotify` check before building the invalid chain on them;
- Core stops its node with the `stop` RPC; `NodeAdapter.stop`
  (`node.py`) terminates the process, and bitcoind runs the command on
  either;
- each command quotes the path it names with `shlex.quote`, for
  `-blocknotify` the directory with the hash appended after it, where
  Core's wraps the whole path in double quotes.

`feature_notifications_bitcoind_test.py` and
`feature_notifications_btclib_node_test.py` run them,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import shlex
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "a_large_work_invalid_chain_is_alerted",
    "every_new_tip_is_notified",
    "the_shutdown_is_notified",
]

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# Core's own `block_count`
_BLOCK_COUNT = 10

# Core's own count of invalid blocks: the chain must be more than six
# blocks longer than the node's own to raise the warning
_INVALID_BLOCKS = 7

# Core's own `LARGE_WORK_INVALID_CHAIN_WARNING`
_LARGE_WORK_INVALID_CHAIN_WARNING = (
    "Warning: Found invalid chain more than 6 blocks longer than our best"
    " chain. This could be due to database corruption or consensus"
    " incompatibility with peers."
)

# the same warning in a build that does not name the invalid chain, as
# its command receives it: `SanitizeString` (`src/util/strencodings.cpp`)
# drops the `!` after "peers"
_PEERS_DISAGREE_WARNING = (
    "Warning: We do not appear to fully agree with our peers You may need"
    " to upgrade, or other nodes may need to upgrade."
)

# `OP_TRUE`: what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"


def _node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    option: str,
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Build a node over a data directory in `tmp_path`, given `option`."""
    rpc_port, p2p_port = free_ports(2)
    return make_adapter(
        cls, executable, tmp_path / "datadir", rpc_port, p2p_port, [option]
    )


def every_new_tip_is_notified(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-blocknotify`'s command runs once per block the node mines.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory and the
        command's directory go.
    :param skip_counts: the session's own tally.
    """
    blocknotify_dir = tmp_path / "blocknotify"
    blocknotify_dir.mkdir()
    command = f"echo > {shlex.quote(str(blocknotify_dir))}/%s"
    node = _node(make_adapter, cls, executable, tmp_path, f"-blocknotify={command}")
    require(Capability.BLOCK_NOTIFY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    try:
        node.start()
        blocks = node.mine(_BLOCK_COUNT)

        wait_until(lambda: len(list(blocknotify_dir.iterdir())) == _BLOCK_COUNT)
        assert sorted(blocks) == sorted(p.name for p in blocknotify_dir.iterdir())
    finally:
        node.stop()


def _invalid_chain(node: NodeAdapter) -> list[Block]:
    """Return `_INVALID_BLOCKS` blocks extending the tip, each overpaying.

    Core's own loop over `create_block`: each coinbase pays one satoshi
    more than the subsidy, which makes each block invalid.
    """
    tip = node.rpc.call("getbestblockhash")
    height = node.rpc.call("getblockcount") + 1
    block_time = node.rpc.call("getblockheader", [tip])["time"] + 1
    previous = bytes.fromhex(tip)
    blocks: list[Block] = []
    for _ in range(_INVALID_BLOCKS):
        coinbase = build_coinbase(
            height, _OP_TRUE, fees=1, halving_interval=_HALVING_INTERVAL
        )
        candidate = build_block(
            previous,
            [coinbase],
            datetime.fromtimestamp(block_time, UTC),
            REGTEST_POW_LIMIT_BITS,
        )
        solved = mine(candidate.header)
        assert solved is not None
        block = Block(solved, candidate.transactions, check_validity=False)
        blocks.append(block)
        previous = block.header.hash
        height += 1
        block_time += 1
    return blocks


def a_large_work_invalid_chain_is_alerted(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    names_the_invalid_chain: Callable[[NodeAdapter], bool],
) -> None:
    """Check `-alertnotify`'s command reports an invalid chain with more work.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory and the alert
        file go.
    :param skip_counts: the session's own tally.
    :param names_the_invalid_chain: whether the running build raises
        Core's own wording of the warning, rather than the one saying it
        does not fully agree with its peers.
    """
    alertnotify_file = tmp_path / "alertnotify.txt"
    command = f"echo %s >> {shlex.quote(str(alertnotify_file))}"
    node = _node(make_adapter, cls, executable, tmp_path, f"-alertnotify={command}")
    require(Capability.ALERT_NOTIFY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    try:
        node.start()
        node.mine(_BLOCK_COUNT)

        invalid_blocks = _invalid_chain(node)
        for block in invalid_blocks:
            node.rpc.call(
                "submitheader", [block.header.serialize(check_validity=False).hex()]
            )
        # the tip first, as Core does: the node's best invalid block is
        # then the chain's tip rather than its first block
        for block in reversed(invalid_blocks):
            node.rpc.call("submitblock", [block.serialize(check_validity=False).hex()])

        warning = (
            _LARGE_WORK_INVALID_CHAIN_WARNING
            if names_the_invalid_chain(node)
            else _PEERS_DISAGREE_WARNING
        )
        wait_until(alertnotify_file.is_file)
        wait_until(lambda: warning in alertnotify_file.read_text(encoding="utf-8"))
    finally:
        node.stop()


def the_shutdown_is_notified(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-shutdownnotify`'s command runs once the node is stopped.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory and the
        command's file go.
    :param skip_counts: the session's own tally.
    """
    shutdownnotify_file = tmp_path / "shutdownnotify.txt"
    command = f"echo > {shlex.quote(str(shutdownnotify_file))}"
    node = _node(make_adapter, cls, executable, tmp_path, f"-shutdownnotify={command}")
    require(Capability.SHUTDOWN_NOTIFY, node.capabilities, skip_counts)
    try:
        node.start()
        node.stop()

        wait_until(shutdownnotify_file.is_file)
    finally:
        node.stop()
