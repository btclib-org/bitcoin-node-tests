# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_presegwit_node_upgrade`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_presegwit_node_upgrade.py`
(`fad7bd9ba3eef03fcdd7cb17011ea0c6e483c767`, 2026-01-14) and ported,
an option-family test
([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)):
`-testactivationheight=segwit@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds segwit inactive until a chosen height, blocks are mined below it
over `submitblock` (`Capability.MINE`), and the node is then restarted
with a lower height its chain already runs past.

Every assertion of Core's own file is kept: a fresh chain with segwit
inactive; the mined height; the restart refused, its exit code non-zero
and its whole stderr equal to Core's own `expected_msg` -- Core's own
`ErrorMatch.FULL_TEXT`, the default `assert_start_raises_init_error`
applies; and, restarted with `-reindex` added, a chain one block short of
the lower height with segwit active. Dropped is the empty stderr Core's
own `TestNode.stop_node` expects of every stop: a check its harness makes
around each stop rather than one this file makes, and `NodeAdapter.stop`
makes it for no test.

The blocks are mined in the shape Core's own `generate` gives them rather
than `MiniWallet.generate`'s: a coinbase carrying the witness commitment
and no witness nonce. `GenerateCoinbaseCommitment` (`src/validation.cpp`)
writes the commitment into every block `CreateNewBlock`
(`src/node/miner.cpp`) assembles, and its own
`UpdateUncommittedBlockStructures` adds the nonce only once segwit is
active, so every block Core's own file mines carries the one without the
other. Under segwit's rules `CheckWitnessMalleation` refuses that pair
(`bad-witness-nonce-size`), which is what stops the reindexed chain one
block short of the lower height. A `MiniWallet` block carries neither,
and a block committing to no witness and carrying none is valid either
side of activation: measured against the pinned bitcoind `31.1`, a chain
of them reindexes to its full mined height instead.

`NodeAdapter.start` (`node.py`) waits for the RPC to answer and no
longer, where Core's own `TestNode.wait_for_rpc_connection` also waits
for `getmempoolinfo`'s `loaded`, which the import thread of
`src/init.cpp` sets only once `ImportBlocks` has returned: this test
waits for it after the reindexing start, the one start here after which
a height it reads could still be moved by a running import.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import os
import re
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from btclib.block.block import Block, witness_commitment_output
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS
from btclib.tx import Tx

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports
from bitcoin_node_tests.timeout_factor import scaled

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own three values: the activation height the node first runs
# with, how many blocks are mined below it, and the lower height the
# restart names
_SEGWIT_HEIGHT = 10
_MINED = 8
_LOWER_SEGWIT_HEIGHT = 5

# Core's own `expected_msg`, `os.linesep` included
_EXPECTED_MSG = (
    f"Witness data for blocks after height {_LOWER_SEGWIT_HEIGHT} requires "
    f"validation. Please restart with -reindex..{os.linesep}"
    "Please restart with -reindex or -reindex-chainstate to recover."
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)

# Core's own `TestNode.wait_until` default, scaled as Core scales it
_IMPORT_TIMEOUT = 60.0

# BIP141's reserved value as Core's own `GenerateCoinbaseCommitment` fills
# it, the commitment's second preimage half
_ZERO_WITNESS_NONCE = b"\x00" * 32


def _uncommitted_block(adapter: BitcoindAdapter, wallet: MiniWallet) -> Block:
    """Return a solved block on `adapter`'s own tip, shaped as Core mines it.

    Its coinbase carries the witness commitment and no witness nonce,
    this module's own docstring has why. Built here rather than through
    `MiniWallet.generate`, whose blocks carry neither.

    :param adapter: the node whose own tip this block extends.
    :param wallet: whose own `script_pub_key` the coinbase pays.
    """
    tip = adapter.rpc.call("getbestblockhash")
    height = adapter.rpc.call("getblockcount") + 1
    median_time = adapter.rpc.call("getblockchaininfo")["mediantime"]
    coinbase = build_coinbase(height, wallet.script_pub_key)
    committed = Tx(
        version=coinbase.version,
        lock_time=coinbase.lock_time,
        vin=coinbase.vin,
        vout=[
            *coinbase.vout,
            witness_commitment_output([coinbase], _ZERO_WITNESS_NONCE),
        ],
    )
    block_time = max(int(datetime.now(UTC).timestamp()), median_time + 1)
    candidate = build_block(
        bytes.fromhex(tip),
        [committed],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
    )
    solved = mine(candidate.header)
    if solved is None:
        err_msg = f"no nonce solved height {height} within the search bound"
        raise RuntimeError(err_msg)
    return Block(solved, candidate.transactions, check_validity=False)


def _wait_for_import(adapter: BitcoindAdapter) -> None:
    """Wait for `getmempoolinfo`'s `loaded`, as Core's own start does.

    :param adapter: the node whose own block import is awaited.
    :raises TimeoutError: the mempool never reported loaded.
    """
    timeout = scaled(_IMPORT_TIMEOUT)
    deadline = time.monotonic() + timeout
    while not adapter.rpc.call("getmempoolinfo")["loaded"]:
        if time.monotonic() >= deadline:
            err_msg = f"the block import did not finish within {timeout} s"
            raise TimeoutError(err_msg)
        time.sleep(0.1)


def _segwit_active(adapter: BitcoindAdapter) -> bool:
    """Core's own `softfork_active(node, "segwit")` (`util.py`).

    :param adapter: the node asked.
    """
    deployments = adapter.rpc.call("getdeploymentinfo")["deployments"]
    return bool(deployments["segwit"]["active"])


def test_a_pre_segwit_chain_needs_a_reindex_to_upgrade(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A lower segwit height refuses to start until `-reindex` is added."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-testactivationheight=segwit@{_SEGWIT_HEIGHT}",),
    )
    adapter.start()
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        assert adapter.rpc.call("getblockcount") == 0
        assert not _segwit_active(adapter)

        wallet = MiniWallet(adapter)
        for _ in range(_MINED):
            block = _uncommitted_block(adapter, wallet)
            answer = adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
            assert answer is None
        assert adapter.rpc.call("getblockcount") == _MINED

        adapter.stop()
        lower = f"-testactivationheight=segwit@{_LOWER_SEGWIT_HEIGHT}"
        with pytest.raises(RuntimeError) as refused:
            adapter.restart([lower])
        early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
        assert early_exit is not None
        assert int(early_exit[1]) != 0
        assert early_exit[2] == _EXPECTED_MSG

        adapter.restart(["-reindex", lower])
        _wait_for_import(adapter)
        assert adapter.rpc.call("getblockcount") == _LOWER_SEGWIT_HEIGHT - 1
        assert _segwit_active(adapter)
    finally:
        adapter.stop()
