# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_net`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/rpc_net.py`: `rpc_net_test.py` beside
this module holds each body, run here against bitcoind, which declares
every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.rpc_net_test import (
    a_node_is_added_listed_and_removed,
    a_peer_s_service_flags_are_named,
    addpeeraddress_fills_the_address_tables,
    getaddrmaninfo_counts_the_addresses_of_each_network,
    getnodeaddresses_answers_from_the_address_table,
    getrawaddrman_lists_the_address_tables,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_node_is_added_listed_and_removed(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_node_is_added_listed_and_removed(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_a_peer_s_service_flags_are_named(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_peer_s_service_flags_are_named(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_addpeeraddress_fills_the_address_tables(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    addpeeraddress_fills_the_address_tables(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_getaddrmaninfo_counts_the_addresses_of_each_network(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getaddrmaninfo_counts_the_addresses_of_each_network(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_getnodeaddresses_answers_from_the_address_table(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getnodeaddresses_answers_from_the_address_table(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_getrawaddrman_lists_the_address_tables(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getrawaddrman_lists_the_address_tables(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
