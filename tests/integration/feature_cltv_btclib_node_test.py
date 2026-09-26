# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_cltv`, rewritten on this harness: btclib-node.

The same requests `feature_cltv_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.TEST_ACTIVATION_HEIGHT` is not declared -- the same
measurement `feature_dersig_btclib_node_test.py`'s own docstring already
has -- so this counts a skip rather than a run, before any node is ever
spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_cltv_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_cltv_activates_one_block_before_the_configured_height(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_version_3_block_is_refused_once_active(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_version_3_block_is_logged_once_active(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    require(Capability.DEBUG_LOG, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
