# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_fastprune`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_fastprune.py` (`fa5f29774872`,
2025-12-16), the option and MiniWallet families together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-fastprune` (`Capability.FASTPRUNE`) shrinks bitcoind's block files to
64 KiB (`BlockManager::FindNextBlockPos`, `src/node/blockstorage.cpp`),
and a block larger than that must still be stored and connected rather
than crash or freeze the node. `MiniWallet.create_self_transfer`
(`Capability.MINE`) funds the one transaction, whose witness gains a
BIP341 annex of `0x10000` bytes past its leading `0x50`, and
`MiniWallet.generate`'s own `confirm` mines it.

Core's own claim in full, reached another way: Core mines the block
with `generateblock`, paying `raw(55)`; this mines it client-side over
`submitblock`, paying the wallet's own script, which is how every
`MiniWallet` block here is mined. The block count asserted is this
chain's own rather than Core's `201`: Core starts from a cached chain
of `200` blocks, this from a fresh one of `COINBASE_MATURITY + 1`. Two
assertions are added, that the new tip carries the transaction and is
larger than the annex, so a block that never grew past a block file
cannot pass.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from btclib.script.witness import Witness
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# BIP341's annex: the last witness element, recognised by its leading
# 0x50, here padded to one byte past `-fastprune`'s own 64 KiB block file
_ANNEX = b"\x50" + b"\xff" * 0x10000


def test_a_block_larger_than_a_block_file_is_stored(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """A block past `-fastprune`'s own block-file size connects all the same."""
    require(Capability.FASTPRUNE, BitcoindAdapter.capabilities, skip_counts)
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        free_port(),
        free_port(),
        extra_args=("-fastprune",),
    )
    adapter.start()
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        wallet.generate(COINBASE_MATURITY + 1)
        tx = wallet.create_self_transfer()
        tx_in = tx.vin[0]
        tx_in.script_witness = Witness([*tx_in.script_witness.stack, _ANNEX])
        wallet.generate(1, confirm=[tx])
        assert adapter.rpc.call("getblockcount") == COINBASE_MATURITY + 2
        block = adapter.rpc.call("getblock", [adapter.rpc.call("getbestblockhash")])
        assert tx.id.hex() in block["tx"]
        assert block["size"] > len(_ANNEX)
    finally:
        adapter.stop()
