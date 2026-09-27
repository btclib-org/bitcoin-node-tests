# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_disconnect_ban`, its `disconnectnode` half: bitcoind.

Read from Core's `test/functional/p2p_disconnect_ban.py`:
`p2p_disconnect_ban_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_disconnect_ban_test import (
    disconnectnode_drops_a_peer_by_address_and_by_node_id,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_disconnectnode_drops_a_peer_by_address_and_by_node_id(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    disconnectnode_drops_a_peer_by_address_and_by_node_id(bitcoind_cluster, skip_counts)
