# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_blocksxor`, one body over either node.

Read from Core's `test/functional/feature_blocksxor.py`
(`fa5f29774872`, 2025-12-16), the option, MiniWallet and disk families
together ([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node under `-blocksxor=1` (`Capability.BLOCKS_XOR`) and `-fastprune`
(`Capability.FASTPRUNE`) spreads the blocks `MiniWallet` mines
(`Capability.MINE`) over several block files and as many undo files, in
Core's own layout (`Capability.BLK_FILES`), obfuscated with the key
`blocks/xor.dat` holds. Stopped, and every one of those files XORed back
to plain, the node refuses to restart under `-blocksxor=0` while that
key is stored, in Core's own words; with the key file removed it starts
under `-blocksxor=0`, `verifychain` checks every block and its undo
data, and the key file it writes again is all zeros.

`-blocksxor=1` is Core's default, so a node ignoring it obfuscates the
files all the same; the refusal is what reads the option. And a start
over a block directory already holding files, and no key file, writes an
all-zero key whatever `-blocksxor` says (`InitBlocksdirXorKey`,
`src/node/blockstorage.cpp`), so Core's last step would pass on a node
ignoring the option too. This asserts more than Core's file, so that it
cannot: the first block file, read raw, does not open with the network
magic and does once XORed with the key; and a second node, over a fresh
data directory started under `-blocksxor=0`, writes an all-zero key,
where a start without it writes a random one.

Core's chain is the framework's cached one; this node mines its own, a
coin matured before the transactions Core pads to its `target_vsize`.
The nodes are built through `make_adapter`
(`tests/integration/conftest.py`), since the test rewrites files inside
a data directory and starts each node with an option from its first
start.

`feature_blocksxor_bitcoind_test.py` and
`feature_blocksxor_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import magic_from_chain
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = ["block_files_are_obfuscated_with_the_xor_key"]

# Core's own loop: how many padded transactions it sends, one per block,
# and the virtual size each is padded to
_TRANSACTIONS = 5
_TARGET_VSIZE = 20_000

# Core's `NULL_BLK_XOR_KEY` (`test_framework/test_node.py`), its own
# `NUM_XOR_BYTES` zero octets
_NULL_KEY = bytes(8)

# the start of Core's own refusal (`InitBlocksdirXorKey`), which goes on
# to name the key stored and its path
_XOR_KEY_STORED = (
    "The blocksdir XOR-key can not be disabled when a random key was already stored!"
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)


def _xor(data: bytes, key: bytes) -> bytes:
    """Core's `util_xor` (`test_framework/util.py`), at offset zero."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    datadir: Path,
    extra_args: list[str],
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Build a node over `datadir`, started with `extra_args` by default."""
    rpc_port, p2p_port = free_ports(2)
    return make_adapter(cls, executable, datadir, rpc_port, p2p_port, extra_args)


def block_files_are_obfuscated_with_the_xor_key(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-blocksxor`'s key obfuscates the block and undo files.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the nodes' own data directories go.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    node = _node(
        make_adapter, cls, executable, datadir, ["-blocksxor=1", "-fastprune=1"]
    )
    fresh = _node(make_adapter, cls, executable, tmp_path / "fresh", ["-blocksxor=0"])
    for capability in (
        Capability.BLOCKS_XOR,
        Capability.FASTPRUNE,
        Capability.MINE,
        Capability.BLK_FILES,
    ):
        require(capability, node.capabilities, skip_counts)
    blocks = datadir / "regtest" / "blocks"
    key_path = blocks / "xor.dat"
    try:
        node.start()
        wallet = MiniWallet(node)
        wallet.generate(COINBASE_MATURITY + 1)
        for _ in range(_TRANSACTIONS):
            tx = wallet.send_self_transfer(target_vsize=_TARGET_VSIZE)
            wallet.generate(1, confirm=[tx])

        block_files = sorted(blocks.glob("blk[0-9][0-9][0-9][0-9][0-9].dat"))
        undo_files = sorted(blocks.glob("rev[0-9][0-9][0-9][0-9][0-9].dat"))
        assert len(block_files) == len(undo_files)
        assert len(block_files) > 1

        node.stop()
        key = key_path.read_bytes()
        assert key != _NULL_KEY
        magic = magic_from_chain("regtest")
        first = block_files[0].read_bytes()[: len(magic)]
        assert first != magic
        assert _xor(first, key) == magic
        for data_file in block_files + undo_files:
            data_file.write_bytes(_xor(data_file.read_bytes(), key))

        with pytest.raises(RuntimeError) as refused:
            node.restart(["-blocksxor=0"])
        early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
        assert early_exit is not None
        assert int(early_exit[1]) != 0
        assert _XOR_KEY_STORED in early_exit[2]
        assert f"Stored key: '{key.hex()}'" in early_exit[2]

        key_path.unlink()
        node.restart(["-blocksxor=0"])
        assert node.rpc.call("verifychain", [2, 0]) is True
        assert key_path.read_bytes() == _NULL_KEY
        node.stop()

        fresh.start()
        fresh.stop()
        assert (tmp_path / "fresh" / "regtest" / "blocks" / "xor.dat").read_bytes() == (
            _NULL_KEY
        )
    finally:
        node.stop()
        fresh.stop()
