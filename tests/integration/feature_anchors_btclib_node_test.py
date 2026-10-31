# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_anchors`, rewritten on tf2's own harness: btclib-node.

`feature_anchors_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Each body has the node dial the test, which asks
for `Capability.TYPED_OUTBOUND`, declared per build (`btclib_node.py`'s
own docstring): a build without it is a counted skip. Past it the
block-relay-only body is a counted skip on `Capability.DEBUG_LOG`,
bitcoind's alone, and the onion body on `Capability.PROXY`, which no
build declares.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_anchors_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_anchors_test import (
    block_relay_only_peers_are_the_anchors,
    onion_anchor_is_dumped_and_dialled,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_block_relay_only_peers_are_the_anchors(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    block_relay_only_peers_are_the_anchors(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_onion_anchor_is_dumped_and_dialled(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    onion_anchor_is_dumped_and_dialled(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
