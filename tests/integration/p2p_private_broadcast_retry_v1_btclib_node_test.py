# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_private_broadcast_retry_v1`, on this harness: btclib-node.

`p2p_private_broadcast_retry_v1_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test is a counted skip on
`Capability.PRIVATE_BROADCAST`, which `btclib_node.py`'s own docstring has
no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/p2p_private_broadcast_retry_v1_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.p2p_private_broadcast_retry_v1_test import (
    v1_retry_goes_through_the_tor_proxy,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_v1_retry_goes_through_the_tor_proxy(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    v1_retry_goes_through_the_tor_proxy(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
