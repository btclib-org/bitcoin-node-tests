# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_net`, rewritten on tf2's own harness: btcd.

`rpc_net_test.py` beside this module is the body, run here against btcd,
a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_net_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
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
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_node_is_added_listed_and_removed(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_peer_s_service_flags_are_named(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_peer_s_service_flags_are_named(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_addpeeraddress_fills_the_address_tables(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    addpeeraddress_fills_the_address_tables(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_getaddrmaninfo_counts_the_addresses_of_each_network(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getaddrmaninfo_counts_the_addresses_of_each_network(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_getnodeaddresses_answers_from_the_address_table(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getnodeaddresses_answers_from_the_address_table(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_getrawaddrman_lists_the_address_tables(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getrawaddrman_lists_the_address_tables(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
