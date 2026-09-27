# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addr_relay`, rewritten on this repository's own harness.

Read from Core's `test/functional/p2p_addr_relay.py`: `p2p_addr_relay_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_addr_relay_test import (
    oversized_addr_disconnects_the_peer,
    oversized_addr_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_addr_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    oversized_addr_disconnects_the_peer(bitcoind_adapter)


def test_oversized_addr_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    oversized_addr_is_logged(bitcoind_adapter, skip_counts)
