# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_versionbits_warning`, one body over either node.

Read from Core's `test/functional/feature_versionbits_warning.py`
(`5bd990a3ddb1`, 2026-06-03), the option and the disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node started with `-alertnotify` (`Capability.ALERT_NOTIFY`) is sent
blocks from a peer that signal a version bit no deployment uses. It
raises no warning after a period in which fewer blocks than the threshold
signal it. After a period reaching the threshold and one more, and a
restart, it reports "Unknown new rules activated" in `getmininginfo`'s
and `getnetworkinfo`'s `warnings`, and its command appends that warning
to a file.

In between, blocks reaching the threshold on a bit BIP323 reserves are
checked to raise no warning on a build carrying BIP323; a build without
it warns for that bit as for any other, and the runner says which build
is running.

The node mines the blocks that pad each period (`Capability.MINE`), as
Core's own `generatetoaddress` does. The signalling blocks are built with
btclib in the shape of Core's own `create_block`, each one second after
the last, and sent unasked over a `Peer`, as Core sends each `msg_block`.

What differs from Core's file:

- the check on the reserved bit runs only on a build carrying BIP323,
  where Core's file runs it on every build;
- the command quotes the alert file's path with `shlex.quote`, where
  Core's wraps it in double quotes;
- each check that no warning is reported uses `search` over the joined
  `warnings`, where Core's `match` reads only the start of it: bitcoind
  lists a versionbits warning ahead of its own, `src/node/warnings.h`
  keying them kernel first, and a node that is not bitcoind need not.

`feature_versionbits_warning_bitcoind_test.py` and
`feature_versionbits_warning_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
import shlex
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bitcoin_core_rpc import magic_from_chain
from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import VERSION, mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.consensus import CONSENSUS_PARAMS
from btclib.p2p import BlockPayload

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports, wait_until
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = ["unknown_rules_raise_a_warning"]

_MAGIC = magic_from_chain("regtest")

_HALVING_INTERVAL = CONSENSUS_PARAMS["regtest"].subsidy_halving_interval

# Core's own `VB_PERIOD` and `VB_THRESHOLD`: regtest's own versionbits
# period and threshold (`src/kernel/chainparams.cpp`)
_VB_PERIOD = 144
_VB_THRESHOLD = 108

# Core's own `VB_UNKNOWN_BIT` and `VB_IGNORED_BIT`: a bit no regtest
# deployment uses, and one BIP323 reserves; `VERSION` is Core's own
# `VB_TOP_BITS`
_VB_UNKNOWN_BIT = 3
_VB_UNKNOWN_VERSION = VERSION | (1 << _VB_UNKNOWN_BIT)
_VB_IGNORED_BIT = 5
_VB_IGNORED_VERSION = VERSION | (1 << _VB_IGNORED_BIT)

# Core's own `WARN_UNKNOWN_RULES_ACTIVE` and `VB_PATTERN`
_WARN_UNKNOWN_RULES_ACTIVE = (
    f"Unknown new rules activated (versionbit {_VB_UNKNOWN_BIT})"
)
_VB_PATTERN = re.compile("Unknown new rules activated.*versionbit")

# the alert file Core's own `setup_network` names
_ALERT_FILE_NAME = "alert.txt"

# `OP_TRUE`: what Core's own `create_coinbase` pays
_OP_TRUE = b"\x51"


def _send_blocks_with_version(
    peer: Peer, node: NodeAdapter, count: int, version: int
) -> None:
    """Core's own `send_blocks_with_version`: `count` blocks, then a ping.

    Each extends the last, one second after it, the first extending the
    node's tip.
    """
    tip = node.rpc.call("getbestblockhash")
    height = node.rpc.call("getblockcount")
    block_time = node.rpc.call("getblockheader", [tip])["time"] + 1
    previous = bytes.fromhex(tip)
    for _ in range(count):
        height += 1
        coinbase = build_coinbase(height, _OP_TRUE, halving_interval=_HALVING_INTERVAL)
        candidate = build_block(
            previous,
            [coinbase],
            datetime.fromtimestamp(block_time, UTC),
            REGTEST_POW_LIMIT_BITS,
            version=version,
        )
        solved = mine(candidate.header)
        assert solved is not None
        block = Block(solved, candidate.transactions, check_validity=False)
        peer.send(
            BlockPayload(block, include_witness=True, check_validity=False),
            check_validity=False,
        )
        block_time += 1
        previous = block.header.hash
    peer.sync_with_ping()


def _warnings(node: NodeAdapter, method: str) -> str:
    """Return `method`'s own `warnings`, joined by commas."""
    warnings = node.rpc.call(method)["warnings"]
    assert isinstance(warnings, list)
    return ",".join(warnings)


def _assert_no_versionbits_warning(node: NodeAdapter) -> None:
    """Assert neither `getmininginfo` nor `getnetworkinfo` reports one."""
    assert not _VB_PATTERN.search(_warnings(node, "getmininginfo"))
    assert not _VB_PATTERN.search(_warnings(node, "getnetworkinfo"))


def _out_of_ibd(node: NodeAdapter) -> bool:
    """Whether `getblockchaininfo` reports the node out of initial download."""
    return not node.rpc.call("getblockchaininfo")["initialblockdownload"]


def _connect(node: NodeAdapter) -> Peer:
    """Core's own `add_p2p_connection`: a handshake, then a ping round trip."""
    peer = Peer(node.p2p_address, _MAGIC)
    try:
        peer.handshake()
        peer.sync_with_ping()
    except BaseException:
        peer.close()
        raise
    return peer


def unknown_rules_raise_a_warning(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    ignores_reserved_bits: Callable[[NodeAdapter], bool],
) -> None:
    """Check unknown rules activated are warned about, and reserved bits not.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory and the alert
        file go.
    :param skip_counts: the session's own tally.
    :param ignores_reserved_bits: whether the running build carries
        BIP323, and so warns for no bit it reserves.
    """
    alert_file = tmp_path / _ALERT_FILE_NAME
    alert_file.touch()
    command = f"echo %s >> {shlex.quote(str(alert_file))}"
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(
        cls,
        executable,
        tmp_path / "datadir",
        rpc_port,
        p2p_port,
        [f"-alertnotify={command}"],
    )
    require(Capability.ALERT_NOTIFY, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    try:
        node.start()
        with _connect(node) as peer:
            # one period of the node's own blocks
            node.mine(_VB_PERIOD)

            # a period in which fewer blocks than the threshold signal
            # the unknown bit: no warning
            _send_blocks_with_version(
                peer, node, _VB_THRESHOLD - 1, _VB_UNKNOWN_VERSION
            )
            node.mine(_VB_PERIOD - _VB_THRESHOLD + 1)
            _assert_no_versionbits_warning(node)

            # a period in which the threshold signals a reserved bit,
            # and one more to activate it, out of initial download: no
            # warning, on a build carrying BIP323
            _send_blocks_with_version(peer, node, _VB_THRESHOLD, _VB_IGNORED_VERSION)
            node.mine(_VB_PERIOD - _VB_THRESHOLD)
            node.mine(_VB_PERIOD)
            wait_until(lambda: _out_of_ibd(node))
            if ignores_reserved_bits(node):
                _assert_no_versionbits_warning(node)

            # a period in which the threshold signals the unknown bit,
            # and one more to activate it
            _send_blocks_with_version(peer, node, _VB_THRESHOLD, _VB_UNKNOWN_VERSION)
            node.mine(_VB_PERIOD - _VB_THRESHOLD)
            node.mine(_VB_PERIOD)

        # the node warns once per start about unknown rules activated
        node.restart()

        # one block out of initial download, one more for the warning
        node.mine(1)
        wait_until(lambda: _out_of_ibd(node))
        node.mine(1)
        assert _WARN_UNKNOWN_RULES_ACTIVE in _warnings(node, "getmininginfo")
        assert _WARN_UNKNOWN_RULES_ACTIVE in _warnings(node, "getnetworkinfo")
        wait_until(
            lambda: (
                _VB_PATTERN.search(alert_file.read_text(encoding="utf-8")) is not None
            )
        )
    finally:
        node.stop()
