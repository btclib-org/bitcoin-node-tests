# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own lifecycle against a real node: btclib-node.

`adapter_lifecycle_test.py` beside this module is the body of `stop`
reporting a node killed out from under the adapter
([ISS 84](https://github.com/btclib-org/bitcoin-node-tests/issues/84))
and of `mine` extending the tip
([ISS 56](https://github.com/btclib-org/bitcoin-node-tests/issues/56)),
run here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `mine` is a counted skip on `Capability.MINE`
for a build that does not declare it.

`adapter_lifecycle_bitcoind_test.py` keeps the scenarios about bitcoind's
wallet and its server timeout; its docstring lists them.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/adapter_lifecycle_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.adapter_lifecycle_test import (
    mine_extends_the_tip_by_the_blocks_it_returns,
    stop_reports_a_node_killed_out_from_under_it,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_stop_reports_a_node_killed_out_from_under_it(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path
) -> None:
    """The target: a node killed before `stop`."""
    stop_reports_a_node_killed_out_from_under_it(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_mine_extends_the_tip_by_the_blocks_it_returns(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: each `mine` moves the tip onto its last hash."""
    mine_extends_the_tip_by_the_blocks_it_returns(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
