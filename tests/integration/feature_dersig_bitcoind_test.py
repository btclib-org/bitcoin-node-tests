# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dersig`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_dersig.py` (`fab352053d6e`,
2026-04-16) and narrowed to the two of its own checks the option and
MiniWallet families reach together (issue #14 of
[ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-testactivationheight=dersig@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds BIP66 inactive until a chosen height, and `MiniWallet.generate`
(`Capability.MINE`) mines to it with no node wallet.

A smaller claim than Core's own file, declared rather than silent:
Core's own closing checks build a non-DER-compliant signature and show
that a block carrying it is refused once BIP66 activates -- a real
ECDSA spend `MiniWallet`'s own `ADDRESS_OP_TRUE` coins do not carry
(`mini_wallet.py`'s own docstring is why: btclib's own signing surface
is left to btclib's own suite, rule 7 of
[ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220)).
Kept, and read at the pinned bitcoind `31.1` rather than assumed:
`getdeploymentinfo`'s own `bip66` entry, which transitions from inactive
to active one block before the configured height -- the same "not
active as of current tip, but the next block must obey rules" boundary
Core's own file comments -- and the buried-deployment version floor
Core's own file also checks with a version-2 block once BIP66 is
active, `bad-version(0x00000002)` both in `submitblock`'s own answer and
in the node's own debug log (`ProcessNewBlock: AcceptBlock FAILED
(bad-version(0x00000002), ...)`, `src/validation.cpp`'s own
`ContextualCheckBlockHeader`). Not narrowed further than Core's own
file on this specific check: measured live against the pinned `31.1`,
a version-2 block is refused the same way both before and after BIP66's
own configured height, BIP65's own default floor (`-testactivationheight`
touching only the deployment it names) already requiring version 4 from
height 1 -- so Core's own file does not attempt the before/after
comparison for this check either, only the after-activation refusal.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from btclib.block.block import Block
from btclib.block.build import build_block, build_coinbase
from btclib.block.mining import mine
from btclib.block.proof_of_work import REGTEST_POW_LIMIT_BITS

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# Core's own file hardcodes 102; this harness needs only that the height is
# reached in a handful of mined blocks, not that it matches Core's own value
_DERSIG_HEIGHT = 12


def _start_adapter(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path
) -> BitcoindAdapter:
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=(f"-testactivationheight=dersig@{_DERSIG_HEIGHT}",),
    )
    adapter.start()
    return adapter


def _low_version_block(
    adapter: BitcoindAdapter, wallet: MiniWallet, version: int
) -> Block:
    """Return a solved, unsubmitted block extending `adapter`'s own tip.

    Built directly rather than through `MiniWallet.generate`: that method
    carries no `version` parameter of its own, needing none for any port
    before this one.

    :param adapter: the node whose own tip this block extends.
    :param wallet: whose own `script_pub_key` the coinbase pays.
    :param version: the block header's own version.
    """
    tip = adapter.rpc.call("getbestblockhash")
    height = adapter.rpc.call("getblockcount") + 1
    median_time = adapter.rpc.call("getblockchaininfo")["mediantime"]
    coinbase = build_coinbase(height, wallet.script_pub_key)
    block_time = max(int(datetime.now(UTC).timestamp()), median_time + 1)
    candidate = build_block(
        bytes.fromhex(tip),
        [coinbase],
        datetime.fromtimestamp(block_time, UTC),
        REGTEST_POW_LIMIT_BITS,
        version=version,
    )
    solved = mine(candidate.header)
    if solved is None:
        err_msg = f"no nonce solved height {height} within the search bound"
        raise RuntimeError(err_msg)
    return Block(solved, candidate.transactions, check_validity=False)


def test_dersig_activates_one_block_before_the_configured_height(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """`getdeploymentinfo`'s own `bip66` entry tracks the configured height."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66 == {"type": "buried", "active": False, "height": _DERSIG_HEIGHT}

        wallet.generate(_DERSIG_HEIGHT - 2)
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66["active"] is False

        wallet.generate(1)  # tip is now one block before the configured height
        bip66 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip66"]
        assert bip66["active"] is True
    finally:
        adapter.stop()


def test_a_block_below_the_minimum_version_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Once BIP66 is active, a version-2 block never becomes the tip."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_DERSIG_HEIGHT - 1)
        old_tip = adapter.rpc.call("getbestblockhash")

        block = _low_version_block(adapter, wallet, version=2)
        answer = adapter.rpc.call(
            "submitblock", [block.serialize(check_validity=False).hex()]
        )

        assert answer == "bad-version(0x00000002)"
        assert adapter.rpc.call("getbestblockhash") == old_tip
    finally:
        adapter.stop()


def test_a_block_below_the_minimum_version_is_logged(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The same refusal, in bitcoind's own debug log wording."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(make_adapter, bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_DERSIG_HEIGHT - 1)

        block = _low_version_block(adapter, wallet, version=2)
        with assert_debug_log(adapter.debug_log_path, ["bad-version(0x00000002)"]):
            adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
    finally:
        adapter.stop()
