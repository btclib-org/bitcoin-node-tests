# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_proxy.py`:
`feature_proxy_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_proxy_test import (
    onion_reaches_tor_through_a_proxy_of_its_own,
    proxy_reaches_every_network_through_one_proxy,
    proxyrandomize_gives_each_connection_credentials_of_its_own,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_proxy_reaches_every_network_through_one_proxy(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    proxy_reaches_every_network_through_one_proxy(bitcoind_cluster, skip_counts)


def test_onion_reaches_tor_through_a_proxy_of_its_own(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    onion_reaches_tor_through_a_proxy_of_its_own(bitcoind_cluster, skip_counts)


def test_proxyrandomize_gives_each_connection_credentials_of_its_own(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    proxyrandomize_gives_each_connection_credentials_of_its_own(
        bitcoind_cluster, skip_counts
    )
