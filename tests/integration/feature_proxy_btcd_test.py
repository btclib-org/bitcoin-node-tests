# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, rewritten on tf2's own harness: btcd.

`feature_proxy_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_proxy_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_proxy_test import (
    cjdnsreachable_reaches_cjdns_through_the_proxy,
    clearing_the_ipv4_proxy_clears_the_name_proxy,
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

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_proxy_reaches_every_network_through_one_proxy(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    proxy_reaches_every_network_through_one_proxy(btcd_cluster, skip_counts)


def test_onion_reaches_tor_through_a_proxy_of_its_own(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    onion_reaches_tor_through_a_proxy_of_its_own(btcd_cluster, skip_counts)


def test_proxyrandomize_gives_each_connection_credentials_of_its_own(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    proxyrandomize_gives_each_connection_credentials_of_its_own(
        btcd_cluster, skip_counts
    )


def test_ipv6_loopback_proxy_reaches_every_network_but_onion(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    ipv6_loopback_proxy_reaches_every_network_but_onion(btcd_cluster, skip_counts)


def test_cjdnsreachable_reaches_cjdns_through_the_proxy(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    cjdnsreachable_reaches_cjdns_through_the_proxy(btcd_cluster, skip_counts)


def test_unix_socket_proxy_reaches_every_network_but_i2p(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    unix_socket_proxy_reaches_every_network_but_i2p(btcd_cluster, skip_counts)


def test_onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    onion_through_a_unix_socket_is_the_proxy_of_onion_alone(btcd_cluster, skip_counts)


def test_i2psam_is_the_proxy_of_i2p_alone(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    i2psam_is_the_proxy_of_i2p_alone(btcd_cluster, skip_counts)


def test_proxy_network_suffix_sets_the_proxy_of_that_network(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    proxy_network_suffix_sets_the_proxy_of_that_network(btcd_cluster, skip_counts)


def test_clearing_the_ipv4_proxy_clears_the_name_proxy(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    clearing_the_ipv4_proxy_clears_the_name_proxy(btcd_cluster, skip_counts)


def test_malformed_proxy_or_onion_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    malformed_proxy_or_onion_is_refused(btcd_cluster, skip_counts)


def test_malformed_i2psam_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    malformed_i2psam_is_refused(btcd_cluster, skip_counts)


def test_onlynet_refuses_a_network_it_cannot_reach(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    onlynet_refuses_a_network_it_cannot_reach(btcd_cluster, skip_counts)
