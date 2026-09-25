# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_cltv`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_cltv.py` (`fab352053d6e`,
2026-04-16) and narrowed the same way
`feature_dersig_bitcoind_test.py`'s own docstring narrows its sibling
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-testactivationheight=cltv@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds BIP65 inactive until a chosen height, `MiniWallet.generate`
(`Capability.MINE`) mines to it.

Dropped: Core's own closing checks, which build transactions carrying
`OP_CHECKLOCKTIMEVERIFY` and show each of BIP65's five failure reasons is
refused once the fork activates -- `MiniWallet`'s own `ADDRESS_OP_TRUE`
coins spend through a single fixed tapscript leaf
(`mini_wallet.py`'s own docstring), and a caller-chosen leaf carrying
that opcode is a new capability for it rather than a fact this file's own
option and MiniWallet mechanisms already reach. Kept: `getdeploymentinfo`'s
own `bip65` entry, transitioning one block before the configured height
the same way `bip66`'s does, and the buried-deployment version floor a
version-3 block trips once BIP65 is active -- `bad-version(0x00000003)`,
`submitblock`'s own answer and the node's own debug log line, both
measured live against the pinned `31.1`. This one file's own check *is*
isolated from the other buried deployments' own default floors, unlike
`feature_dersig_bitcoind_test.py`'s: a version-3 block already satisfies
BIP66's own default floor (active from height 1 regardless of this
file's own `-testactivationheight`), so version 3 is refused only once
this file's own configured height is reached, and Core's own file checks
exactly this version.

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
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own file hardcodes 111; this harness needs only that the height is
# reached in a handful of mined blocks, not that it matches Core's own value
_CLTV_HEIGHT = 12


def _start_adapter(bitcoind_path: str, tmp_path: Path) -> BitcoindAdapter:
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        free_port(),
        free_port(),
        extra_args=(f"-testactivationheight=cltv@{_CLTV_HEIGHT}",),
    )
    adapter.start()
    return adapter


def _low_version_block(
    adapter: BitcoindAdapter, wallet: MiniWallet, version: int
) -> Block:
    """Return a solved, unsubmitted block extending `adapter`'s own tip.

    Shared shape with `feature_dersig_bitcoind_test.py`'s own private
    helper of the same name and signature -- not factored out into
    `src/`, both being test-only and neither used by any other module.

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


def test_cltv_activates_one_block_before_the_configured_height(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`getdeploymentinfo`'s own `bip65` entry tracks the configured height."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        bip65 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip65"]
        assert bip65 == {"type": "buried", "active": False, "height": _CLTV_HEIGHT}

        wallet.generate(_CLTV_HEIGHT - 2)
        bip65 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip65"]
        assert bip65["active"] is False

        wallet.generate(1)  # tip is now one block before the configured height
        bip65 = adapter.rpc.call("getdeploymentinfo")["deployments"]["bip65"]
        assert bip65["active"] is True
    finally:
        adapter.stop()


def test_a_version_3_block_is_refused_once_active(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """Once BIP65 is active, a version-3 block never becomes the tip."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_CLTV_HEIGHT - 1)
        old_tip = adapter.rpc.call("getbestblockhash")

        block = _low_version_block(adapter, wallet, version=3)
        answer = adapter.rpc.call(
            "submitblock", [block.serialize(check_validity=False).hex()]
        )

        assert answer == "bad-version(0x00000003)"
        assert adapter.rpc.call("getbestblockhash") == old_tip
    finally:
        adapter.stop()


def test_a_version_3_block_is_logged_once_active(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """The same refusal, in bitcoind's own debug log wording."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = _start_adapter(bitcoind_path, tmp_path)
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        require(Capability.DEBUG_LOG, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(_CLTV_HEIGHT - 1)

        block = _low_version_block(adapter, wallet, version=3)
        with assert_debug_log(adapter.debug_log_path, ["bad-version(0x00000003)"]):
            adapter.rpc.call(
                "submitblock", [block.serialize(check_validity=False).hex()]
            )
    finally:
        adapter.stop()
