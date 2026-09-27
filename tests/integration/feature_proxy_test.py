# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_proxy`, one body over either node.

Read from Core's `test/functional/feature_proxy.py` (`f82043af507a`,
2026-06-30) and ported in part, the first file of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47):
a node given a SOCKS5 proxy dials its peers through it, and
`getnetworkinfo` reports which proxy each network is reached by.
`Capability.PROXY` is what a node declares for `-proxy`, `-onion` and
`-proxyrandomize`, and `socks5.Socks5Proxy` is the proxy.

Kept, one test each, are Core's nodes given `-proxy` alone, `-onion`
beside it with `-proxyrandomize` off, and `-proxyrandomize` against a
proxy offering username/password. Each dials Core's own addresses --
IPv4, IPv6, onion and a DNS name -- with `addnode`'s `onetry`, reads the
request its proxy recorded, and asserts the network `getpeerinfo`
reports for the peer. The proxy holds each connection open, so the peer
is still listed when that read comes, well inside the node's own
`-peertimeout`: the proxies of Core's own file close it, and Core's own
check asserts nothing of a peer `getpeerinfo` no longer lists.

Still owed to ISS 47: Core's IPv6-loopback proxy, its unix-socket
proxies, `-cjdnsreachable`, the `-onion` node's `-i2psam`, `-onlynet`,
`-proxy`'s per-network `=<network>` suffix and every start Core's file
expects refused. Core's check that `localaddresses` is empty is dropped
rather than owed: this adapter's own `-bind` already empties it without
a proxy (`TF2.md`'s paragraph on `feature_discover.py` has the
measurement).

Each node is also started with `-dnsseed` off, as Core's own
`write_config` (`test_framework/util.py`) starts every node: through a
proxy, a regtest node asks for its chain's own `dummySeed.invalid.` as
well, and that request can reach the proxy ahead of one of the test's
own (measured against the pinned release).

`feature_proxy_bitcoind_test.py` and `feature_proxy_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.socks5 import AddressType, Socks5Proxy, Socks5Request

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "onion_reaches_tor_through_a_proxy_of_its_own",
    "proxy_reaches_every_network_through_one_proxy",
    "proxyrandomize_gives_each_connection_credentials_of_its_own",
]

# the networks `getnetworkinfo` reports, Core's own `NETWORKS`
_NETWORKS = frozenset({"ipv4", "ipv6", "onion", "i2p", "cjdns"})


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
_DNS_NAME = _Target(
    "node.noumenon:8333", b"node.noumenon", 8333, "not_publicly_routable"
)


def _endpoint(proxy: Socks5Proxy) -> str:
    """Return `proxy`'s address as `-proxy` and `getnetworkinfo` spell it."""
    host, port = proxy.address
    return f"{host}:{port}"


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


def _assert_every_network_but_i2p(
    networks: dict[str, dict[str, object]], proxy: Socks5Proxy
) -> None:
    """Check the report of a node given `proxy` alone, with `-proxyrandomize`.

    I2P's own proxy is `-i2psam`'s, which the node is not given, so it
    reports none; every other network reports `proxy`, with randomized
    credentials. Onion is reachable through `-proxy`; I2P is not without
    `-i2psam`, nor CJDNS without `-cjdnsreachable`.
    """
    for name, network in networks.items():
        expected = ("", False) if name == "i2p" else (_endpoint(proxy), True)
        assert (network["proxy"], network["proxy_randomize_credentials"]) == expected
    assert networks["onion"]["reachable"] is True
    assert networks["i2p"]["reachable"] is False
    assert networks["cjdns"]["reachable"] is False


def proxy_reaches_every_network_through_one_proxy(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxy` alone takes a peer of every network Core's test dials.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy() as proxy:
        node.restart([f"-proxy={_endpoint(proxy)}", "-proxyrandomize=1", "-dnsseed=0"])
        for target in (_IPV4, _IPV6, _ONION, _DNS_NAME):
            _dial(node, target, proxy, credentials=False)
        _assert_every_network_but_i2p(_networks(node), proxy)


def onion_reaches_tor_through_a_proxy_of_its_own(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-onion` takes the onion connection `-proxy` does not.

    Core's node given `-onion`, its `-i2psam` left to a later part of
    ISS 47. The onion proxy offers username/password, and
    `-proxyrandomize` off has the node send it none.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy() as proxy, Socks5Proxy(authentication=True) as onion:
        node.restart(
            [
                f"-proxy={_endpoint(proxy)}",
                f"-onion={_endpoint(onion)}",
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
            assert networks[name]["proxy"] == _endpoint(proxy)
            assert networks[name]["proxy_randomize_credentials"] is False
        assert networks["onion"]["proxy"] == _endpoint(onion)
        assert networks["onion"]["proxy_randomize_credentials"] is False
        assert networks["onion"]["reachable"] is True


def proxyrandomize_gives_each_connection_credentials_of_its_own(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxyrandomize` sends each connection distinct credentials.

    A proxy offering username/password, which the node authenticates to
    with a pair no other connection of its own uses.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PROXY, node.capabilities, skip_counts)
    with Socks5Proxy(authentication=True) as proxy:
        node.restart([f"-proxy={_endpoint(proxy)}", "-proxyrandomize=1", "-dnsseed=0"])
        requests = [
            _dial(node, target, proxy, credentials=True)
            for target in (_IPV4, _IPV6, _ONION, _DNS_NAME)
        ]
        pairs = {(request.username, request.password) for request in requests}
        assert len(pairs) == len(requests)
        _assert_every_network_but_i2p(_networks(node), proxy)
