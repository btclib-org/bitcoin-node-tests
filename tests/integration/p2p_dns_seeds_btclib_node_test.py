# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_dns_seeds`, rewritten on this harness: btclib-node.

`p2p_dns_seeds_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
The test is a counted skip on `Capability.DNS_SEED`, which
`btclib_node.py`'s own docstring has no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_dns_seeds_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.p2p_dns_seeds_test import (
    dns_seeds_are_queried_only_when_peers_are_wanting,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_dns_seeds_are_queried_only_when_peers_are_wanting(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    dns_seeds_are_queried_only_when_peers_are_wanting(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
