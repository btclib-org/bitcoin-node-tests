# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_proxy.py`:
`feature_proxy_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for,
`Capability.PROXY_PER_NETWORK` only where its build takes the suffix.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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


def test_ipv6_loopback_proxy_reaches_every_network_but_onion(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    ipv6_loopback_proxy_reaches_every_network_but_onion(bitcoind_cluster, skip_counts)


def test_cjdnsreachable_reaches_cjdns_through_the_proxy(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    cjdnsreachable_reaches_cjdns_through_the_proxy(bitcoind_cluster, skip_counts)


def test_unix_socket_proxy_reaches_every_network_but_i2p(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    unix_socket_proxy_reaches_every_network_but_i2p(bitcoind_cluster, skip_counts)


def test_onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
        bitcoind_cluster, skip_counts
    )


def test_i2psam_is_the_proxy_of_i2p_alone(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    i2psam_is_the_proxy_of_i2p_alone(bitcoind_cluster, skip_counts)


def test_proxy_network_suffix_sets_the_proxy_of_that_network(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    proxy_network_suffix_sets_the_proxy_of_that_network(bitcoind_cluster, skip_counts)


def test_malformed_proxy_or_onion_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    malformed_proxy_or_onion_is_refused(bitcoind_cluster, skip_counts)


def test_malformed_i2psam_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    malformed_i2psam_is_refused(bitcoind_cluster, skip_counts)


def test_onlynet_refuses_a_network_it_cannot_reach(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    onlynet_refuses_a_network_it_cannot_reach(bitcoind_cluster, skip_counts)
