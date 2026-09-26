# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_dust`, rewritten on this harness: btclib-node.

The same requests `mempool_dust_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.PERMIT_BARE_MULTISIG` is not declared: measured against
`cli.py`'s registered options, `_build_parser` on the released build and
`_OPTIONS` on `main`, `-permitbaremultisig` is not one of its registered
flags -- a counted skip on that capability alone, before any node is
ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_dust_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_value_clearly_below_the_dust_threshold_is_refused(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.PERMIT_BARE_MULTISIG` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.PERMIT_BARE_MULTISIG, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_value_clearly_above_the_dust_threshold_is_allowed(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.PERMIT_BARE_MULTISIG` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.PERMIT_BARE_MULTISIG, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_dustrelayfee_zero_waives_the_dust_check(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.PERMIT_BARE_MULTISIG` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.PERMIT_BARE_MULTISIG, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.DUST_RELAY_FEE, BtclibNodeAdapter.capabilities, skip_counts)
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
