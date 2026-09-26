# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_dersig`, rewritten on this harness: btclib-node.

The same requests `feature_dersig_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.TEST_ACTIVATION_HEIGHT` is not declared: measured against
`cli.py`'s own `_build_parser` (`btclib_node.py`'s own docstring has the
same measurement for `-uacomment`), `-testactivationheight` is not one
of its registered flags -- a counted skip on that capability alone,
before any node is ever spawned, the way
`feature_uacomment_btclib_node_test.py`'s own skip already is.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/feature_dersig_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_dersig_activates_one_block_before_the_configured_height(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_block_below_the_minimum_version_is_refused(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.TEST_ACTIVATION_HEIGHT` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.TEST_ACTIVATION_HEIGHT, BtclibNodeAdapter.capabilities, skip_counts
    )
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_a_block_below_the_minimum_version_is_logged(
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
