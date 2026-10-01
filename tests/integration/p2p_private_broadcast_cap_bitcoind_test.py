# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_private_broadcast_cap`, on this repository's harness.

Read from Core's `test/functional/p2p_private_broadcast_cap.py`:
`p2p_private_broadcast_cap_test.py` beside this module is the body, run
here against bitcoind. A build before `v31.0` has no `-privatebroadcast`,
and the test is a counted skip on `Capability.PRIVATE_BROADCAST` there.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.p2p_private_broadcast_cap_test import (
    private_broadcast_queue_is_capped,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_private_broadcast_queue_is_capped(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    private_broadcast_queue_is_capped(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
