# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_handshake.py`: `p2p_handshake_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_handshake_test import (
    redundant_verack_is_logged,
    redundant_verack_keeps_the_connection,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_redundant_verack_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    redundant_verack_keeps_the_connection(bitcoind_adapter)


def test_redundant_verack_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    redundant_verack_is_logged(bitcoind_adapter, skip_counts)
