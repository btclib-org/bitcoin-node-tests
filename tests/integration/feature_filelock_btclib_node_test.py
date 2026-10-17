# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_filelock`, rewritten on this harness: btclib-node.

`feature_filelock_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). btclib-node locks the data directory and then the
blocks directory before either store opens
([ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_filelock_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_filelock_test import (
    second_instance_on_same_blocksdir_refuses_to_start,
    second_instance_on_same_datadir_refuses_to_start,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_second_instance_on_same_datadir_refuses_to_start(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: a second node over the same datadir is refused."""
    second_instance_on_same_datadir_refuses_to_start(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_second_instance_on_same_blocksdir_refuses_to_start(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a second node over the first's blocksdir is refused."""
    second_instance_on_same_blocksdir_refuses_to_start(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
