# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_addr_selfannouncement`, rewritten on this repository's harness.

Read from Core's `test/functional/p2p_addr_selfannouncement.py`:
`p2p_addr_selfannouncement_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_addr_selfannouncement_test import (
    externalip_bypasses_onlynet,
    self_announcement_to_inbound_peers,
    self_announcement_to_inbound_peers_is_logged,
    self_announcement_to_outbound_peers,
    self_announcement_to_outbound_peers_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_self_announcement_to_inbound_peers(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    self_announcement_to_inbound_peers(bitcoind_cluster, skip_counts)


def test_self_announcement_to_inbound_peers_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    self_announcement_to_inbound_peers_is_logged(bitcoind_cluster, skip_counts)


def test_self_announcement_to_outbound_peers(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    self_announcement_to_outbound_peers(bitcoind_cluster, skip_counts)


def test_self_announcement_to_outbound_peers_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    self_announcement_to_outbound_peers_is_logged(bitcoind_cluster, skip_counts)


def test_externalip_bypasses_onlynet(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    externalip_bypasses_onlynet(bitcoind_cluster, skip_counts)
