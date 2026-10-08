# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, one body over either node.

Read from Core's `test/functional/feature_proxy.py` (`f82043af507a`,
2026-06-30), the first file of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47):
a node given a SOCKS5 proxy dials its peers through it, `getnetworkinfo`
reports which proxy each network is reached by, and a start naming no
usable proxy is refused. `socks5.Socks5Proxy` is the proxy, and each test
asks for the capability of every option it sets or whose refusal it
reads: `Capability.PROXY` for
`-proxy`, `-onion` and `-proxyrandomize`, `Capability.PROXY_PER_NETWORK`
for `-proxy`'s `=<network>` suffix, `Capability.CJDNS` for
`-cjdnsreachable`, `Capability.I2P_SAM` for `-i2psam` and
`Capability.ONLYNET` for `-onlynet`.

Each of Core's nodes is a test of its own, on a fresh node. Its
`node_test` dials Core's own addresses -- IPv4, IPv6, onion, CJDNS where
`-cjdnsreachable` is given, and a DNS name -- with `addnode`'s `onetry`;
each is read back as the request its proxy recorded and as the network
`getpeerinfo` reports for the peer. The proxy holds each connection open,
so the peer is still listed when that read comes, well inside the node's
own `-peertimeout`: the proxies of Core's own file close it, and Core's
own check asserts nothing of a peer `getpeerinfo` no longer lists.

Core's IPv6-loopback and unix-socket proxies are asked for
unconditionally, where Core's file leaves out the nodes needing either on
a host without it. A host lacking one is not a capability the node
lacks, so there is no counted skip to take, and btclib-org/.github's
`reusable-integration-bitcoind.yml` fails the `bitcoind` job on any other
skip.

Core's node given `-i2psam` is also given `-proxy` and `-onion`, which
the `-onion` test here already covers: the `-i2psam` test gives the node
`-i2psam` alone, so that it asks for `Capability.I2P_SAM` alone.

Every start Core's file expects refused is refused here, with a non-zero
exit and a stderr equal to Core's own `expected_msg` whole, the
`ErrorMatch.FULL_TEXT` comparison `assert_start_raises_init_error` makes
by default. A node without `Capability.PROXY_PER_NETWORK` reads a
`-proxy` suffix as part of the port, so the starts giving one expect its
refusal of that port instead.

The start Core's file expects to succeed, `-onlynet=onion`
beside `-listenonion=1`, is dropped: `BitcoindAdapter._command` sets
`-listenonion=0` itself, so `_check_extra_args` (`node.py`) refuses the
option, and that same argv is what refuses `-onlynet=onion` given alone,
the way Core's `-listenonion=0` does.

Core's check that `localaddresses` is empty is dropped: this adapter's
own `-bind` already empties it without a proxy: measured against the
pinned bitcoind, `getnetworkinfo`'s `localaddresses` answers empty whether
`-discover` is passed bare or given its disabling value.

Each node given a proxy is also started with `-dnsseed` off, as Core's
own `write_config` (`test_framework/util.py`) starts every node: through
a proxy, a regtest node asks for its chain's own `dummySeed.invalid.` as
well, and that request can reach the proxy ahead of one of the test's
own (measured against the pinned release).

`feature_proxy_bitcoind_test.py` and `feature_proxy_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

import re
import socket
from typing import TYPE_CHECKING, NamedTuple

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.socks5 import AddressType, Socks5Proxy, Socks5Request

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "cjdnsreachable_reaches_cjdns_through_the_proxy",
    "i2psam_is_the_proxy_of_i2p_alone",
    "ipv6_loopback_proxy_reaches_every_network_but_onion",
    "malformed_i2psam_is_refused",
    "malformed_proxy_or_onion_is_refused",
    "onion_reaches_tor_through_a_proxy_of_its_own",
    "onion_through_a_unix_socket_is_the_proxy_of_onion_alone",
    "onlynet_refuses_a_network_it_cannot_reach",
    "proxy_network_suffix_sets_the_proxy_of_that_network",
    "proxy_reaches_every_network_through_one_proxy",
    "proxyrandomize_gives_each_connection_credentials_of_its_own",
    "unix_socket_proxy_reaches_every_network_but_i2p",
]

# the networks `getnetworkinfo` reports, Core's own `NETWORKS`
_NETWORKS = frozenset({"ipv4", "ipv6", "onion", "i2p", "cjdns"})

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)

# Core's own `-i2psam`, which its file never connects to
_I2P_SAM = "127.0.0.1:7656"

# a unix socket path longer than a socket address holds, Core's own
_LONG_UNIX_PATH = f"unix:{'x' * 1000}"

# Core's own `expected_msg` for each start its file expects refused
_PROXY_HOST = "Error: Invalid -proxy address or hostname: 'abc..abc:23456'"
_PROXY_PORT = "Error: Invalid port specified in -proxy: '192.0.0.1:def'"
_ONION_HOST = "Error: Invalid -onion address or hostname: 'xyz..xyz:23456'"
_ONION_PORT = "Error: Invalid port specified in -onion: '192.0.0.1:def'"
_PROXY_TRAILING_EQUALS = (
    "Error: Invalid -proxy address or hostname, ends with '=': '127.0.0.1:9050='"
)
_PROXY_UNKNOWN_NETWORK = (
    "Error: Unrecognized network in -proxy='127.0.0.1:9050=foo': 'foo'"
)
_PROXY_LONG_UNIX_PATH = (
    f"Error: Invalid -proxy address or hostname: '{_LONG_UNIX_PATH}'"
)
_I2PSAM_HOST = "Error: Invalid -i2psam address or hostname: 'def..def:23456'"
_I2PSAM_PORT = "Error: Invalid port specified in -i2psam: '192.0.0.1:def'"
_ONLYNET_I2P = (
    "Error: Outbound connections restricted to i2p (-onlynet=i2p) but "
    "-i2psam is not provided"
)
_ONLYNET_CJDNS = (
    "Error: Outbound connections restricted to CJDNS (-onlynet=cjdns) but "
    "-cjdnsreachable is not provided"
)
_ONLYNET_ONION_FORBIDDEN = (
    "Error: Outbound connections restricted to Tor (-onlynet=onion) but the "
    "proxy for reaching the Tor network is explicitly forbidden: -onion=0"
)
_ONLYNET_ONION_MISSING = (
    "Error: Outbound connections restricted to Tor (-onlynet=onion) but the "
    "proxy for reaching the Tor network is not provided: none of -proxy, "
    "-onion or -listenonion is given"
)
_ONLYNET_UNKNOWN = "Error: Unknown network specified in -onlynet: 'abc'"


class _Target(NamedTuple):
    """An address Core's `node_test` dials, and what the node reports of it."""

    address: str
    host: bytes
    port: int
    network: str


# Core's own `node_test` addresses, in its order
_IPV4 = _Target("15.61.23.23:1234", b"15.61.23.23", 1234, "ipv4")
_IPV6 = _Target(
    "[1233:3432:2434:2343:3234:2345:6546:4534]:5443",
    b"1233:3432:2434:2343:3234:2345:6546:4534",
    5443,
    "ipv6",
)
_ONION = _Target(
    "pg6mmjiyjmcrsslvykfwnntlaru7p5svn6y2ymmju6nubxndf4pscryd.onion:8333",
    b"pg6mmjiyjmcrsslvykfwnntlaru7p5svn6y2ymmju6nubxndf4pscryd.onion",
    8333,
    "onion",
)
_CJDNS = _Target("[fc00:1:2:3:4:5:6:7]:8888", b"fc00:1:2:3:4:5:6:7", 8888, "cjdns")
_DNS_NAME = _Target(
    "node.noumenon:8333", b"node.noumenon", 8333, "not_publicly_routable"
)


def _dial(
    node: NodeAdapter, target: _Target, proxy: Socks5Proxy, *, credentials: bool
) -> Socks5Request:
    """Have `node` dial `target`, and check what `proxy` and the node recorded.

    The node names every host by name, `DOMAINNAME`, an IPv4 or an IPv6
    address included, as Core's own `node_test` asserts. `v2transport` is
    off, as Core's own is, so a refused BIP324 handshake schedules no v1
    retry through the same proxy.

    :param credentials: whether the request is expected to carry them;
        where not, it is checked to carry none.
    :returns: the request, for a caller comparing several.
    """
    node.rpc.call("addnode", [target.address, "onetry", False])
    request = proxy.next_request()
    assert request.address_type == AddressType.DOMAINNAME
    assert request.host == target.host
    assert request.port == target.port
    if not credentials:
        assert request.username is None
        assert request.password is None
    networks = {peer["addr"]: peer["network"] for peer in node.rpc.call("getpeerinfo")}
    assert networks[target.address] == target.network
    return request


def _networks(node: NodeAdapter) -> dict[str, dict[str, object]]:
    """Return `getnetworkinfo`'s `networks`, keyed by each network's name."""
    networks = node.rpc.call("getnetworkinfo")["networks"]
    by_name = {network["name"]: network for network in networks}
    assert by_name.keys() == _NETWORKS
    return by_name


def _proxies(node: NodeAdapter) -> dict[str, object]:
    """Return each network's `proxy` as `getnetworkinfo` reports it."""
    return {name: network["proxy"] for name, network in _networks(node).items()}


def _assert_every_network_but_i2p(
    networks: dict[str, dict[str, object]], endpoint: str, *, cjdns: bool = False
) -> None:
    """Check the report of a node given one proxy, with `-proxyrandomize`.

    I2P's own proxy is `-i2psam`'s, which the node is not given, so it
    reports none; every other network reports `endpoint`, with randomized
    credentials. Onion is reachable through `-proxy`; I2P is not without
    `-i2psam`, nor CJDNS without `-cjdnsreachable`.

    :param cjdns: whether the node was given `-cjdnsreachable`.
    """
    for name, network in networks.items():
        expected = ("", False) if name == "i2p" else (endpoint, True)
        assert (network["proxy"], network["proxy_randomize_credentials"]) == expected
    assert networks["onion"]["reachable"] is True
    assert networks["i2p"]["reachable"] is False
    assert networks["cjdns"]["reachable"] is cjdns


def _port_refusal(arg: str) -> str:
    """Return the refusal of a `-proxy` suffix read as part of the port.

    :param arg: the `-proxy=<value>` argument.
    """
    return f"Error: Invalid port specified in -proxy: '{arg.removeprefix('-proxy=')}'"


def _refusal(node: NodeAdapter, extra_args: list[str]) -> str:
    """Start `node` with `extra_args`, and return the stderr it exits with.

    Core's own `assert_start_raises_init_error`: the start fails, with an
    exit code other than `0`, before its RPC ever answers.

    :param node: a node the caller has stopped.
    :param extra_args: what to start it with.
    """
    with pytest.raises(RuntimeError) as refused:
        node.restart(extra_args)
    early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
    assert early_exit is not None
    assert int(early_exit[1]) != 0
    return early_exit[2].strip()


def proxy_reaches_every_network_through_one_proxy(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxy` alone takes a peer of every network Core's test dials.

    Core's node 0.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy() as proxy:
        node.restart([f"-proxy={proxy.endpoint}", "-proxyrandomize=1", "-dnsseed=0"])
        for target in (_IPV4, _IPV6, _ONION, _DNS_NAME):
            _dial(node, target, proxy, credentials=False)
        _assert_every_network_but_i2p(_networks(node), proxy.endpoint)


def onion_reaches_tor_through_a_proxy_of_its_own(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-onion` takes the onion connection `-proxy` does not.

    Core's node 1, its `-i2psam` left to
    `i2psam_is_the_proxy_of_i2p_alone`. The onion proxy offers
    username/password, and `-proxyrandomize` off has the node send it
    none.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy() as proxy, Socks5Proxy(authentication=True) as onion:
        node.restart(
            [
                f"-proxy={proxy.endpoint}",
                f"-onion={onion.endpoint}",
                "-proxyrandomize=0",
                "-dnsseed=0",
            ]
        )
        for target, through in (
            (_IPV4, proxy),
            (_IPV6, proxy),
            (_ONION, onion),
            (_DNS_NAME, proxy),
        ):
            _dial(node, target, through, credentials=False)
        networks = _networks(node)
        for name in ("ipv4", "ipv6"):
            assert networks[name]["proxy"] == proxy.endpoint
            assert networks[name]["proxy_randomize_credentials"] is False
        assert networks["onion"]["proxy"] == onion.endpoint
        assert networks["onion"]["proxy_randomize_credentials"] is False
        assert networks["onion"]["reachable"] is True


def proxyrandomize_gives_each_connection_credentials_of_its_own(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxyrandomize` sends each connection distinct credentials.

    Core's node 2: a proxy offering username/password, which the node
    authenticates to with a pair no other connection of its own uses.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy(authentication=True) as proxy:
        node.restart([f"-proxy={proxy.endpoint}", "-proxyrandomize=1", "-dnsseed=0"])
        requests = [
            _dial(node, target, proxy, credentials=True)
            for target in (_IPV4, _IPV6, _ONION, _DNS_NAME)
        ]
        pairs = {(request.username, request.password) for request in requests}
        assert len(pairs) == len(requests)
        _assert_every_network_but_i2p(_networks(node), proxy.endpoint)


def ipv6_loopback_proxy_reaches_every_network_but_onion(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a proxy on `::1` takes every network `-noonion` leaves it.

    Core's node 3: the proxy offers username/password, and
    `-proxyrandomize` off has the node send it none. No onion address is
    dialled, as Core's own `node_test` dials none for this node.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy(authentication=True, family=socket.AF_INET6) as proxy:
        node.restart(
            [
                f"-proxy={proxy.endpoint}",
                "-proxyrandomize=0",
                "-noonion",
                "-dnsseed=0",
            ]
        )
        for target in (_IPV4, _IPV6, _DNS_NAME):
            _dial(node, target, proxy, credentials=False)
        networks = _networks(node)
        for name, network in networks.items():
            expected = "" if name in {"onion", "i2p"} else proxy.endpoint
            assert (network["proxy"], network["proxy_randomize_credentials"]) == (
                expected,
                False,
            )
        assert networks["onion"]["reachable"] is False
        assert networks["i2p"]["reachable"] is False
        assert networks["cjdns"]["reachable"] is False


def cjdnsreachable_reaches_cjdns_through_the_proxy(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-cjdnsreachable` takes an `fc00::/8` address as CJDNS.

    Core's node 4: the CJDNS address goes through `-proxy`'s own proxy,
    as its IPv6 one does, and `getpeerinfo` names its network `cjdns`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.CJDNS, node.capabilities, skip_counts)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy() as proxy:
        node.restart(
            [
                f"-proxy={proxy.endpoint}",
                "-proxyrandomize=1",
                "-cjdnsreachable",
                "-dnsseed=0",
            ]
        )
        for target in (_IPV4, _IPV6, _ONION, _CJDNS, _DNS_NAME):
            _dial(node, target, proxy, credentials=False)
        _assert_every_network_but_i2p(_networks(node), proxy.endpoint, cjdns=True)


def unix_socket_proxy_reaches_every_network_but_i2p(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxy=unix:<path>` takes a peer of every network, as one on TCP.

    Core's node 5: the proxy offers username/password, and
    `-proxyrandomize`'s own default has the node send it credentials.
    `getnetworkinfo` reports the path behind `unix:`, with no port.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy(authentication=True, family=socket.AF_UNIX) as proxy:
        node.restart([f"-proxy={proxy.endpoint}", "-dnsseed=0"])
        for target in (_IPV4, _IPV6, _ONION, _DNS_NAME):
            _dial(node, target, proxy, credentials=True)
        _assert_every_network_but_i2p(_networks(node), proxy.endpoint)


def onion_through_a_unix_socket_is_the_proxy_of_onion_alone(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-onion=unix:<path>` alone gives onion a proxy and nothing else.

    Core's node 6, of which Core's file dials nothing.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy(authentication=True, family=socket.AF_UNIX) as proxy:
        node.restart([f"-onion={proxy.endpoint}", "-dnsseed=0"])
        networks = _networks(node)
        for name, network in networks.items():
            expected = (proxy.endpoint, True) if name == "onion" else ("", False)
            assert (
                network["proxy"],
                network["proxy_randomize_credentials"],
            ) == expected
    assert networks["onion"]["reachable"] is True
    assert networks["i2p"]["reachable"] is False
    assert networks["cjdns"]["reachable"] is False


def i2psam_is_the_proxy_of_i2p_alone(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-i2psam` makes I2P reachable, its endpoint I2P's proxy alone.

    Core's node 1's own `-i2psam` and `-i2pacceptincoming=0`, given
    without the `-proxy` and `-onion` beside them there. Nothing listens
    at the endpoint, and nothing needs to: with no incoming I2P
    connection to accept -- the session `CConnman::Start` (`src/net.cpp`)
    opens only where it is asked to -- and no I2P address to dial, the
    node never reaches it, which is Core's own comment on it. Nothing
    reads `-i2pacceptincoming=0` back, as nothing in Core's file does.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.I2P_SAM, node.capabilities, skip_counts)
    node.restart([f"-i2psam={_I2P_SAM}", "-i2pacceptincoming=0"])
    networks = _networks(node)
    for name, network in networks.items():
        expected = _I2P_SAM if name == "i2p" else ""
        assert (network["proxy"], network["proxy_randomize_credentials"]) == (
            expected,
            False,
        )
    assert networks["i2p"]["reachable"] is True


def proxy_network_suffix_sets_the_proxy_of_that_network(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxy=<proxy>=<network>` sets, or removes, one network's proxy.

    Core's own restarts of its node 1: a proxy for IPv6 alone, one each
    for IPv4 and IPv6, onion's overriding the proxy of every network, and
    CJDNS's removed from it. Every network's proxy is compared, where
    Core's file reads only the networks each start names: a proxy for
    IPv4 given without its suffix, before IPv6's own, leaves IPv4 and
    IPv6 reading as Core's check expects, and only the networks it does
    not read tell the two apart. Nothing is dialled, so nothing listens
    at Core's own addresses.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    require(Capability.PROXY_PER_NETWORK, node.capabilities, skip_counts)
    none = dict.fromkeys(_NETWORKS, "")
    for proxies, expected in (
        (["127.6.6.6:6666=ipv6"], {"ipv6": "127.6.6.6:6666"}),
        (
            ["127.4.4.4:4444=ipv4", "127.6.6.6:6666=ipv6"],
            {"ipv4": "127.4.4.4:4444", "ipv6": "127.6.6.6:6666"},
        ),
        (
            ["127.1.1.1:1111", "127.2.2.2:2222=onion"],
            {
                "ipv4": "127.1.1.1:1111",
                "ipv6": "127.1.1.1:1111",
                "onion": "127.2.2.2:2222",
                "cjdns": "127.1.1.1:1111",
            },
        ),
        (
            ["127.1.1.1:1111", "0=cjdns"],
            {
                "ipv4": "127.1.1.1:1111",
                "ipv6": "127.1.1.1:1111",
                "onion": "127.1.1.1:1111",
            },
        ),
    ):
        node.restart([*(f"-proxy={proxy}" for proxy in proxies), "-dnsseed=0"])
        assert _proxies(node) == none | expected


def malformed_proxy_or_onion_is_refused(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a `-proxy` or `-onion` naming no usable proxy refuses to start.

    Core's own invalid hosts and ports for each, a `-proxy` ending in
    `=`, one naming a network Core does not know, and a unix socket path
    longer than a socket address holds. A node without
    `Capability.PROXY_PER_NETWORK` reads a suffix as part of the port, so
    the `-proxy` starts giving one expect its refusal of that port.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    node.stop()
    trailing, unknown = "-proxy=127.0.0.1:9050=", "-proxy=127.0.0.1:9050=foo"
    if Capability.PROXY_PER_NETWORK in node.capabilities:
        trailing_expected, unknown_expected = (
            _PROXY_TRAILING_EQUALS,
            _PROXY_UNKNOWN_NETWORK,
        )
    else:
        trailing_expected, unknown_expected = (
            _port_refusal(trailing),
            _port_refusal(unknown),
        )
    for arg, expected in (
        ("-proxy=abc..abc:23456", _PROXY_HOST),
        ("-proxy=192.0.0.1:def", _PROXY_PORT),
        ("-onion=xyz..xyz:23456", _ONION_HOST),
        ("-onion=192.0.0.1:def", _ONION_PORT),
        (trailing, trailing_expected),
        (unknown, unknown_expected),
        (f"-proxy={_LONG_UNIX_PATH}", _PROXY_LONG_UNIX_PATH),
    ):
        assert _refusal(node, [arg]) == expected


def malformed_i2psam_is_refused(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check an `-i2psam` naming no usable address refuses to start.

    Core's own invalid host and invalid port.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.I2P_SAM, node.capabilities, skip_counts)
    node.stop()
    for arg, expected in (
        ("-i2psam=def..def:23456", _I2PSAM_HOST),
        ("-i2psam=192.0.0.1:def", _I2PSAM_PORT),
    ):
        assert _refusal(node, [arg]) == expected


def onlynet_refuses_a_network_it_cannot_reach(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-onlynet` refuses a network it has no way to reach, or none.

    Core's own refusals: I2P without `-i2psam`, CJDNS without
    `-cjdnsreachable`, onion with its proxy forbidden by `-onion=0` or
    `-noonion`, onion with no proxy at all, and a network Core does not
    know. The wording names the option each network's reach is given by,
    so each capability behind those options is asked for too.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    for capability in (
        Capability.ONLYNET,
        Capability.PROXY,
        Capability.I2P_SAM,
        Capability.CJDNS,
    ):
        require(capability, node.capabilities, skip_counts)
    node.stop()
    for extra_args, expected in (
        (["-onlynet=i2p"], _ONLYNET_I2P),
        (["-onlynet=cjdns"], _ONLYNET_CJDNS),
        (["-onlynet=onion", "-onion=0"], _ONLYNET_ONION_FORBIDDEN),
        (["-onlynet=onion", "-noonion"], _ONLYNET_ONION_FORBIDDEN),
        (["-onlynet=onion"], _ONLYNET_ONION_MISSING),
        (["-onlynet=abc"], _ONLYNET_UNKNOWN),
    ):
        assert _refusal(node, extra_args) == expected
