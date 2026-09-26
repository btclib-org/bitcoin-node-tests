# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_csv_activation`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/feature_csv_activation.py`
(`fab352053d6e`, 2026-04-16) and narrowed to what the option and
MiniWallet families reach together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`-testactivationheight=csv@N` (`Capability.TEST_ACTIVATION_HEIGHT`)
holds BIP68/BIP112/BIP113 -- one deployment, `csv` -- inactive until a
chosen height, `MiniWallet.generate` (`Capability.MINE`) mines to it.

Dropped: Core's own file's whole body, which builds eighty-three inputs
and tests BIP68's relative locktimes, BIP112's `OP_CHECKSEQUENCEVERIFY`
and BIP113's median-time-past cutover against real transactions --
`MiniWallet`'s own `ADDRESS_OP_TRUE` coins spend through a single fixed
tapscript leaf carrying neither opcode. A version this harness could
build needs a caller-chosen leaf for BIP112's opcode, and
`create_self_transfer`'s own `sequence` and `locktime` for BIP68's and
BIP113's fields -- more than this file's own two mechanisms, so it stays
open under
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14).
Kept: `getdeploymentinfo`'s own `csv` entry, transitioning one block
before the configured height the same way `bip66`'s and `bip65`'s do in
`feature_dersig_bitcoind_test.py` and `feature_cltv_bitcoind_test.py`.

Unlike its two siblings, this file needs no `Capability.DEBUG_LOG` row:
CSV carries no buried-deployment version floor of its own -- measured
against `src/validation.cpp`'s own `ContextualCheckBlockHeader`, whose
version check only ever reads `DEPLOYMENT_HEIGHTINCB`, `DEPLOYMENT_DERSIG`
and `DEPLOYMENT_CLTV` -- so there is no version-floor refusal for this
file to observe on the wire or in the log the way its siblings do.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# Core's own file hardcodes 432; this harness needs only that the height is
# reached in a handful of mined blocks, not that it matches Core's own value
_CSV_ACTIVATION_HEIGHT = 12


def test_csv_activates_one_block_before_the_configured_height(
    bitcoind_path: str, tmp_path: Path, skip_counts: SkipCounts
) -> None:
    """`getdeploymentinfo`'s own `csv` entry tracks the configured height."""
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BitcoindAdapter.capabilities, skip_counts
    )
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path,
        free_port(),
        free_port(),
        extra_args=(f"-testactivationheight=csv@{_CSV_ACTIVATION_HEIGHT}",),
    )
    adapter.start()
    try:
        require(Capability.MINE, adapter.capabilities, skip_counts)
        wallet = MiniWallet(adapter)
        csv = adapter.rpc.call("getdeploymentinfo")["deployments"]["csv"]
        assert csv == {
            "type": "buried",
            "active": False,
            "height": _CSV_ACTIVATION_HEIGHT,
        }

        wallet.generate(_CSV_ACTIVATION_HEIGHT - 2)
        csv = adapter.rpc.call("getdeploymentinfo")["deployments"]["csv"]
        assert csv["active"] is False

        wallet.generate(1)  # tip is now one block before the configured height
        csv = adapter.rpc.call("getdeploymentinfo")["deployments"]["csv"]
        assert csv["active"] is True
    finally:
        adapter.stop()
