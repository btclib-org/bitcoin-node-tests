# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_port`, rewritten on this harness: btclib-node.

`feature_port_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.LISTEN_ADDRESS` is declared
by both builds (`btclib_node.py`'s own docstring), and the test is a
counted skip on both, on `Capability.DEBUG_LOG`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_port_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_port_test import (
    port_and_bind_decide_where_the_node_listens,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_port_and_bind_decide_where_the_node_listens(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: where `-port` and `-bind` have btclib-node listen."""
    port_and_bind_decide_where_the_node_listens(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
