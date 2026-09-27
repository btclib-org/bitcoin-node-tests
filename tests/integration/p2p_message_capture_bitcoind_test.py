# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_message_capture`, rewritten on this repository's harness.

Read from Core's `test/functional/p2p_message_capture.py`:
`p2p_message_capture_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.p2p_message_capture_test import messages_are_captured_to_disk

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_messages_are_captured_to_disk(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a peer's messages captured to disk, over bitcoind."""
    messages_are_captured_to_disk(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
