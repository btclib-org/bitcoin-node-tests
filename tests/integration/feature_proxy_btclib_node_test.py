# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, rewritten on this harness: btclib-node.

`feature_proxy_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Every test is a counted skip on the first
capability it asks for: `BtclibNodeAdapter` declares none of
`Capability.PROXY`, `Capability.CJDNS`, `Capability.I2P_SAM` and
`Capability.ONLYNET`, `cli.py` registering none of their flags on the
released build or on `main` (`btclib_node.py`'s own docstring has the
measurement).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_proxy_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_proxy_test import (
    cjdnsreachable_reaches_cjdns_through_the_proxy,
    i2psam_is_the_proxy_of_i2p_alone,
    ipv6_loopback_proxy_reaches_every_network_but_onion,
    malformed_i2psam_is_refused,
    malformed_proxy_or_onion_is_refused,
    onion_reaches_tor_through_a_proxy_of_its_own,
    onion_through_a_unix_socket_is_the_proxy_of_onion_alone,
    onlynet_refuses_a_network_it_cannot_reach,
    proxy_network_suffix_sets_the_proxy_of_that_network,
    proxy_reaches_every_network_through_one_proxy,
    proxyrandomize_gives_each_connection_credentials_of_its_own,
    unix_socket_proxy_reaches_every_network_but_i2p,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_proxy_reaches_every_network_through_one_proxy(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    proxy_reaches_every_network_through_one_proxy(btclib_node_cluster, skip_counts)


def test_onion_reaches_tor_through_a_proxy_of_its_own(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    onion_reaches_tor_through_a_proxy_of_its_own(btclib_node_cluster, skip_counts)


def test_proxyrandomize_gives_each_connection_credentials_of_its_own(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    proxyrandomize_gives_each_connection_credentials_of_its_own(
        btclib_node_cluster, skip_counts
    )


def test_ipv6_loopback_proxy_reaches_every_network_but_onion(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    ipv6_loopback_proxy_reaches_every_network_but_onion(
        btclib_node_cluster, skip_counts
    )


def test_cjdnsreachable_reaches_cjdns_through_the_proxy(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    cjdnsreachable_reaches_cjdns_through_the_proxy(btclib_node_cluster, skip_counts)


def test_unix_socket_proxy_reaches_every_network_but_i2p(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    unix_socket_proxy_reaches_every_network_but_i2p(btclib_node_cluster, skip_counts)


def test_onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
        btclib_node_cluster, skip_counts
    )


def test_i2psam_is_the_proxy_of_i2p_alone(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    i2psam_is_the_proxy_of_i2p_alone(btclib_node_cluster, skip_counts)


def test_proxy_network_suffix_sets_the_proxy_of_that_network(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    proxy_network_suffix_sets_the_proxy_of_that_network(
        btclib_node_cluster, skip_counts
    )


def test_malformed_proxy_or_onion_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    malformed_proxy_or_onion_is_refused(btclib_node_cluster, skip_counts)


def test_malformed_i2psam_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    malformed_i2psam_is_refused(btclib_node_cluster, skip_counts)


def test_onlynet_refuses_a_network_it_cannot_reach(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    onlynet_refuses_a_network_it_cannot_reach(btclib_node_cluster, skip_counts)
