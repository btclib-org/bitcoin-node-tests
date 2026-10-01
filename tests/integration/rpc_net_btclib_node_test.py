# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_net`, rewritten on this harness: btclib-node.

`rpc_net_test.py` beside this module holds each body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Every test is a counted skip: `btclib_node.py`'s
own docstring has no build declaring `Capability.PROXY`,
`Capability.CJDNS` or `Capability.KNOWN_ADDRESSES`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_net_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
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
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_node_is_added_listed_and_removed(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_a_peer_s_service_flags_are_named(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_peer_s_service_flags_are_named(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_addpeeraddress_fills_the_address_tables(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    addpeeraddress_fills_the_address_tables(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_getaddrmaninfo_counts_the_addresses_of_each_network(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getaddrmaninfo_counts_the_addresses_of_each_network(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_getnodeaddresses_answers_from_the_address_table(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getnodeaddresses_answers_from_the_address_table(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_getrawaddrman_lists_the_address_tables(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getrawaddrman_lists_the_address_tables(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
