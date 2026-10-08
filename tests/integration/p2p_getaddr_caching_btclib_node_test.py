# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getaddr_caching`, rewritten on this harness: btclib-node.

`p2p_getaddr_caching_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.LISTEN_ADDRESS` is declared
by both builds (`btclib_node.py`'s own docstring). The test is a counted
skip on both, on `Capability.KNOWN_ADDRESSES`, which neither declares;
nor `Capability.CLOCK`, which it asks for besides.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_getaddr_caching_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.p2p_getaddr_caching_test import (
    getaddr_answers_are_cached_per_bind,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_getaddr_answers_are_cached_per_bind(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: one cached `getaddr` answer per bind, over btclib-node."""
    getaddr_answers_are_cached_per_bind(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
