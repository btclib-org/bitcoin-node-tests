# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_reindex`, one body over either node.

Read from Core's `test/functional/feature_reindex.py` (`9e6546c517cd`,
2026-06-21), the option, disk and log families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node restarted with `-reindex` or `-reindex-chainstate`
(`Capability.REINDEX`) comes back at the height it had; one whose block
file holds a block ahead of its parent reindexes them all the same,
logging the out-of-order block and its child; and one stopped while
reindexing with `-blockfilterindex` does not wipe that index again on
the next start without `-reindex`.

Each step of Core's `run_test` is a test of its own, over a node built
on a data directory of its own through `make_adapter`
(`tests/integration/conftest.py`), since some of them write into it
while the node is stopped. Each mines with `generatetoaddress`
(`Capability.GENERATE`) to Core's own first deterministic address,
`TestNode.PRIV_KEYS`'s own, as Core's `generate` does. Each waits, after
a start, for `getmempoolinfo`'s `loaded` before reading the height, as
Core's `TestNode.wait_for_rpc_connection` waits for a reindex to finish
(`feature_reindex_init_test.py` has the same wait, and why). Core's
interrupted step starts with `wait_for_import=False` and waits for no
import; this waits after its last start all the same, to read the height
there.

The restarts assert more than Core's own file does, so that a node
ignoring the option cannot pass: a `-reindex` start logs "Reindexing
finished", and a `-reindex-chainstate` one logs the wipe of its
`chainstate` directory. The out-of-order test mines its own chain of the
height Core's reaches there, rather than reusing the first test's. The
interrupted reindex logs "Interrupt requested. Exit reindexing.", and
the wipe of the index's own directory, before the next start is asked
about it: the first shows the reindex was stopped before it finished,
which Core's file assumes, and the second is the line that start must
not repeat, matched once where it is expected. That start logs
"Reindexing finished", the stopped reindex carried to its end, and comes
back at the height mined.

A bitcoind before `v30.0` logs that interruption as "Interrupt requested.
Exit ImportBlocks" (bitcoin/bitcoin#32967). No probe tells the two apart,
the node having no option or RPC for it: that build is asked for its own
line, read off its own `getnetworkinfo` `version`
([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)).

`feature_reindex_bitcoind_test.py` and `feature_reindex_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib.p2p import magic_from_chain

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import free_ports, wait_until
from tests.integration.script_verify_flag_test import bitcoind_version

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = [
    "a_reindex_restores_the_height",
    "an_interrupted_reindex_keeps_its_index",
    "blocks_out_of_order_are_reindexed",
]

# Core's own first deterministic address, `TestNode.PRIV_KEYS`
# (`test_framework/test_node.py`), the one its `generate` pays
_ADDRESS = "mjTkW3DjgyZck4KbiRusZsqTgaYTxdSz6z"

# how many blocks each of Core's `reindex` calls mines
_REINDEX_BLOCKS = 3

# Core's own order of its `reindex` calls: `-reindex-chainstate`
# where `justchainstate` is true
_REINDEX_FLAGS = ("-reindex", "-reindex-chainstate", "-reindex", "-reindex-chainstate")

# the height Core's `out_of_order` starts from, what the calls above mine
_OUT_OF_ORDER_HEIGHT = 12

# how many blocks Core's `continue_reindex_after_shutdown` mines, and the
# most a `generatetoaddress` call here asks for
_INTERRUPTED_HEIGHT = 1500
_MINE_CHUNK = 100

# how long the start after the stopped reindex may take to load. The wait
# is this port's own: Core's start at this point waits for no import. It
# is longer than `wait_until`'s default because the resumed reindex, with
# its block filter index, outlasted that default on a loaded integration run
_INTERRUPTED_LOAD_TIMEOUT = 120.0

# a record of a block file: the network magic, then the block's own
# length, little-endian, then the block (`BlockManager::WriteBlock`,
# `src/node/blockstorage.cpp`)
_RECORD_HEADER = 8

# the records `out_of_order` reads: the genesis block, the blocks it
# swaps, and the block after them; and how much of the file it reads to
# find them, Core's own figure
_RECORDS = 4
_PREFIX = 2000

# `blocks_path`'s own `xor.dat`, the key every block file is obfuscated
# with (`NUM_XOR_BYTES`, `test_framework/test_node.py`)
_XOR_KEY_SIZE = 8

# `LoadExternalBlockFile`'s own `LogDebug`s (`src/validation.cpp`), in
# Core's `reindex` category
_OUT_OF_ORDER = (
    "LoadExternalBlockFile: Out of order block",
    "LoadExternalBlockFile: Processing out of order child",
)

# `ImportBlocks`'s own (`src/node/blockstorage.cpp`)
_REINDEX_FINISHED = "Reindexing finished"
_REINDEX_INTERRUPTED = "Interrupt requested. Exit reindexing."

# the same line before `_REINDEX_EXIT_NAMED_VERSION`, naming the function
_REINDEX_INTERRUPTED_BEFORE = "Interrupt requested. Exit ImportBlocks"

# Core's own `CLIENT_VERSION`, at or past which that line says `reindexing`:
# `v30.0`'s (bitcoin/bitcoin#32967). A known limit: a `master` build from
# that change's merge (`6cdc5a90cf`, 2025-07-25) until the version moved to
# `30.99` (`9f744fffc3`, 2025-09-09) reports `299900` and logs the newer
# line all the same, so the interrupted step fails against such a build
_REINDEX_EXIT_NAMED_VERSION = 300000

# `CDBWrapper`'s own (`src/dbwrapper.cpp`), each followed by the path
_WIPING = "Wiping LevelDB in "
_OPENING = "Opening LevelDB in "

# `util::TraceThread`'s own, for the thread that reindexes
_INITLOAD_START = "initload thread start"


def _node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    datadir: Path,
    skip_counts: SkipCounts,
    *capabilities: Capability,
) -> BitcoindAdapter:
    """Build a node over `datadir`, asking `REINDEX` first, then the rest.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param datadir: the node's own data directory, not yet created.
    :param skip_counts: the session's own tally.
    :param capabilities: what the test asks for besides `REINDEX`,
        `GENERATE` and `DEBUG_LOG`.
    :raises TypeError: the node declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, datadir, rpc_port, p2p_port)
    wanted = (
        Capability.REINDEX,
        Capability.GENERATE,
        Capability.DEBUG_LOG,
        *capabilities,
    )
    for capability in wanted:
        require(capability, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node


def _generate(node: BitcoindAdapter, count: int) -> None:
    """Mine `count` blocks to `_ADDRESS`, `_MINE_CHUNK` at a time."""
    while count > 0:
        chunk = min(count, _MINE_CHUNK)
        node.rpc.call("generatetoaddress", [chunk, _ADDRESS])
        count -= chunk


def _mempool_loaded(node: BitcoindAdapter) -> bool:
    """Return `getmempoolinfo`'s own `loaded`."""
    info = node.rpc.call("getmempoolinfo")
    assert isinstance(info, dict)
    return info["loaded"] is True


def _restart_and_load(
    node: BitcoindAdapter, extra_args: list[str], *, timeout: float = 30.0
) -> None:
    """Restart with `extra_args`, and wait for the node to finish loading.

    :param node: the node to restart.
    :param extra_args: what the start appends to the node's own argv.
    :param timeout: how long to wait, `wait_until`'s own.
    """
    node.restart(extra_args)
    wait_until(lambda: _mempool_loaded(node), timeout=timeout)


def _appended(log_path: Path, offset: int) -> str:
    """Return what the node's log gained past `offset`."""
    with log_path.open(encoding="utf-8", errors="replace") as log_file:
        log_file.seek(offset)
        return log_file.read()


def _xor(data: bytes, key: bytes, offset: int) -> bytes:
    """Core's `util_xor` (`test_framework/util.py`): `data` at `offset`."""
    return bytes(b ^ key[(i + offset) % len(key)] for i, b in enumerate(data))


def a_reindex_restores_the_height(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check each reindex comes back at the height mined, Core's `reindex`.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    node = _node(make_adapter, cls, executable, datadir, skip_counts)
    chainstate = datadir / "regtest" / "chainstate"
    expected = {
        "-reindex": _REINDEX_FINISHED,
        "-reindex-chainstate": f"{_WIPING}{chainstate}",
    }
    try:
        node.start()
        for flag in _REINDEX_FLAGS:
            _generate(node, _REINDEX_BLOCKS)
            height = node.rpc.call("getblockcount")
            with assert_debug_log(node.debug_log_path, [expected[flag]]):
                _restart_and_load(node, [flag])
            assert node.rpc.call("getblockcount") == height
    finally:
        node.stop()


def blocks_out_of_order_are_reindexed(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a block file holding a block ahead of its parent reindexes.

    Core's `out_of_order`: the record of the genesis block's child and
    the record after it change places, each obfuscated anew at its own
    new offset.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    node = _node(
        make_adapter, cls, executable, datadir, skip_counts, Capability.BLK_FILES
    )
    blocks = datadir / "regtest" / "blocks"
    try:
        node.start()
        _generate(node, _OUT_OF_ORDER_HEIGHT)
        node.stop()

        key = (blocks / "xor.dat").read_bytes()[:_XOR_KEY_SIZE]
        blk0 = blocks / "blk00000.dat"
        magic = magic_from_chain("regtest")
        with blk0.open("r+b") as block_file:
            plain = _xor(block_file.read(_PREFIX), key, 0)
            records = []
            start = 0
            for _ in range(_RECORDS):
                assert plain[start : start + len(magic)] == magic
                size = int.from_bytes(
                    plain[start + len(magic) : start + _RECORD_HEADER], "little"
                )
                records.append((start, _RECORD_HEADER + size))
                start += _RECORD_HEADER + size
            (_, (second, length), (third, third_length), _) = records
            assert length == third_length
            block_file.seek(second)
            block_file.write(_xor(plain[third : third + length], key, second))
            block_file.write(_xor(plain[second : second + length], key, third))

        with assert_debug_log(node.debug_log_path, _OUT_OF_ORDER):
            _restart_and_load(node, ["-reindex"])
        assert node.rpc.call("getblockcount") == _OUT_OF_ORDER_HEIGHT
    finally:
        node.stop()


def an_interrupted_reindex_keeps_its_index(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check a reindex stopped early leaves the next start its filter index.

    Core's `continue_reindex_after_shutdown`: started with
    `-blockfilterindex` and `-reindex`, and stopped once the thread that
    reindexes has started, the node's next start, without `-reindex`,
    opens the index rather than wiping it.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    node = _node(
        make_adapter,
        cls,
        executable,
        datadir,
        skip_counts,
        Capability.BLOCK_FILTER_INDEX,
    )
    log_path = node.debug_log_path
    index = datadir / "regtest" / "indexes" / "blockfilter" / "basic" / "db"
    try:
        node.start()
        _generate(node, _INTERRUPTED_HEIGHT)
        version = bitcoind_version(node)
        node.stop()

        interrupted = (
            _REINDEX_INTERRUPTED_BEFORE
            if version is not None and version < _REINDEX_EXIT_NAMED_VERSION
            else _REINDEX_INTERRUPTED
        )
        with assert_debug_log(log_path, [f"{_WIPING}{index}", interrupted]):
            offset = log_path.stat().st_size
            node.restart(["-blockfilterindex", "-reindex"])
            wait_until(lambda: _INITLOAD_START in _appended(log_path, offset))
            node.stop()

        offset = log_path.stat().st_size
        with assert_debug_log(log_path, [f"{_OPENING}{index}", _REINDEX_FINISHED]):
            _restart_and_load(
                node, ["-blockfilterindex"], timeout=_INTERRUPTED_LOAD_TIMEOUT
            )
        assert f"{_WIPING}{index}" not in _appended(log_path, offset)
        assert node.rpc.call("getblockcount") == _INTERRUPTED_HEIGHT
    finally:
        node.stop()
