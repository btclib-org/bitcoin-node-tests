# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_private_broadcast`, one body over either node.

Read from Core's `test/functional/p2p_private_broadcast.py`
(`ac6b6c1f06e9`, 2026-08-18): a node given `-privatebroadcast` sends a
transaction submitted over `sendrawtransaction` to peers of Tor or I2P
over short-lived connections of its own, each opened with a `version`
carrying none of the node's own services, clock, addresses, user agent
or height, and keeps it out of its own mempool until a peer sends it
back. `getprivatebroadcastinfo` lists what it is sending, and
`abortprivatebroadcast` stops sending one.

The body asks for `Capability.PRIVATE_BROADCAST`, and for the capability
of every other option its node is given: `PROXY` for `-proxy`, `CJDNS`
for `-cjdnsreachable`, `I2P_SAM` for `-i2psam`, `V2TRANSPORT` for
`-v2transport`, and `PEER_TIMEOUT` for the `-peertimeout` Core's harness
gives every node; `KNOWN_ADDRESSES` for Core's own `fill_node_addrman`
(`test_framework/test_framework.py`), `MINE` for its `MiniWallet`, `CLOCK`
for its `setmocktime` and `DEBUG_LOG` for its log lines. Core's
`-test=addrman`, a test-only option of bitcoind's own, and the `-dnsseed=0`
of Core's `write_config` are passed with no capability of their own.
Every step of Core's file is kept in its order, every assertion with it
but those named below.

`socks5.Socks5Proxy` is Core's proxy, given a `destinations_factory` that
reads the connection's type off the node's own `getpeerinfo` and forwards
it as Core's does: the first private broadcast connection to the second
node, and every other to a `_Destination` of its own -- the first
outbound full-relay one keeping a transaction store as Core's
`P2PDataStore` does, and the one a step asks for sending `relay` off.
`_Destination` is Core's `P2PInterface` behind `start_p2p_listener`
(`test_framework/p2p.py`): a `Listener` read on a thread of its own,
answering a `version` with its own, a `wtxidrelay` and a `verack`, an
`inv` with a `getdata` for what it names and a `ping` with a `pong`.

What differs from Core's file:

- Core's nodes start on its harness's cached chain. Here the first node's
  `MiniWallet` mines a coin to mature for each spend Core's file makes,
  ahead of Core's first step, and the second node is handed each block
  over `submitblock`, so that it holds the coins the first node's
  transactions spend.
- the second node is reached at its one listening address, where Core
  gives it a second one, `-bind=...=onion`, and forwards there:
  `BitcoindAdapter._command` sets `-bind` itself, so `_check_extra_args`
  (`node.py`) refuses the option.
- the last step is dropped. Core restarts the first node with
  `-listenonion` beside no proxy and reads `sendrawtransaction` refusing
  for want of Tor or I2P; `BitcoindAdapter._command` sets
  `-listenonion=0` itself, so the option is refused, and without it a
  node given `-privatebroadcast` and no proxy does not start at all.
- `-dnsseed=0`, a line of Core's `write_config`, is passed on the command
  line: through a proxy, a regtest node asks for its chain's own
  `dummySeed.invalid.` as well, and that connection would reach the
  factory beside the node's own.
- the steps reading a log line do so over `assert_debug_log`, with Core's
  own wait: one read once the block exits where Core's
  `assert_debug_log` reads once, and up to a minute where Core's
  `busy_wait_for_debug_log` waits.
- a private broadcast's `version` addresses are compared as Core's
  `CAddress` reads them, `_as_core_reads`: the services, the port, and
  the last four octets of the address alone.

Two steps are past the pinned release: `getprivatebroadcastinfo` and
`abortprivatebroadcast` refusing a node without `-privatebroadcast`,
bitcoin/bitcoin@7b821ef9b75eb3f7b3363a1bd46981fa72db7dd4, and the
`attempts_remaining` a transaction reports,
bitcoin/bitcoin@fe7d475d450b9aabd549627c6e61024ae45e7a8c. `v32.0rc1` is
the first tag carrying both, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, what that
build answers instead: no transaction and `Transaction not in private
broadcast queue`, and no `attempts_remaining`. A `master` build between
either change's merge and the version's move to `32.99` reads older and
answers the newer way all the same, the constant's own comment having the
commits.

`p2p_private_broadcast_bitcoind_test.py` and
`p2p_private_broadcast_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass, replace
from functools import partial
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError, magic_from_chain
from btclib.p2p import (
    GetData,
    Inv,
    Inventory,
    InventoryType,
    NetworkAddress,
    Ping,
    Pong,
    ServiceFlags,
    TxPayload,
    Verack,
    Version,
    WtxidRelay,
)
from btclib.script.witness import Witness
from btclib.tx import Tx
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import free_ports, wait_until
from bitcoin_node_tests.peer import Listener, Peer
from bitcoin_node_tests.socks5 import Socks5Proxy
from bitcoin_node_tests.timeout_factor import scaled
from tests.integration.mempool_accept_wtxid_test import malleated_package

if TYPE_CHECKING:
    from pathlib import Path

    from btclib.p2p import Message, Payload

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from bitcoin_node_tests.socks5 import Socks5Request
    from tests.conftest import AdapterFactory

__all__ = [
    "malleated_to_invalid_witness",
    "transactions_are_broadcast_privately",
]

_MAGIC = magic_from_chain("regtest")

# Core's own constants, of its file
_P2P_PRIVATE_VERSION = 70016
_NUM_PRIVATE_BROADCAST_PER_TX = 3
_MAX_PRIVATE_BROADCAST_ATTEMPTS = 1000

# the protocol version from which Core's `P2PInterface` answers a
# `version` with a `wtxidrelay` (BIP339)
_WTXID_RELAY_VERSION = 70016

# Core's own `CLIENT_VERSION` (`src/clientversion.h`), the running build's
# own `getnetworkinfo` `version`, at or past which a node without
# `-privatebroadcast` refuses `getprivatebroadcastinfo` and
# `abortprivatebroadcast`, and a transaction reports its
# `attempts_remaining`: `v32.0`'s, `v32.0rc1` being the first tag carrying
# both. A known limit: a `master` build from the first change's merge
# (`1d3bc816c3`, 2026-06-08) or the second's (`ac6b6c1f06`, 2026-08-18)
# until the version moved to `32.99` (`57d3d00130`, 2026-09-11) reports
# `319900` and answers the newer way all the same, so this test fails
# against such a build
_PRIVATE_BROADCAST_RPCS_VERSION = 320000

# Core's own `P2P_SERVICES` (`test_framework/p2p.py`)
_P2P_SERVICES = ServiceFlags.NODE_NETWORK | ServiceFlags.NODE_WITNESS

_USER_AGENT = b"/bitcoin-node-tests:0/"

# Core's own user agent for a private broadcast connection
_PRIVATE_USER_AGENT = b"/pynode:0.0.1/"

# Core's own `wait_until` default, in seconds, the framework's and a
# `P2PInterface`'s alike
_WAIT = 60.0

# the coins Core's file spends: the chain's first, the siblings' parent's,
# and the aborted transaction's and the one sent to a peer relaying none
_COINS_SPENT = 4

# the entries of `getdata` Core's `P2PDataStore` answers from its store
_TX_TYPES = frozenset(
    {InventoryType.MSG_TX, InventoryType.MSG_WTX, InventoryType.MSG_WITNESS_TX}
)

_NOT_ENABLED = (
    "Private broadcast is not enabled. "
    "Ensure you're running Bitcoin Core with -privatebroadcast=1."
)

# Core's own `fill_node_addrman` (`test_framework/test_framework.py`)
# table, the networks this file asks it for, in its order
_ADDRESSES = (
    "20.0.0.1",
    "30.0.0.1",
    "40.0.0.1",
    "50.0.0.1",
    "60.0.0.1",
    "70.0.0.1",
    "80.0.0.1",
    "90.0.0.1",
    "100.0.0.1",
    "110.0.0.1",
    "120.0.0.1",
    "130.0.0.1",
    "140.0.0.1",
    "150.0.0.1",
    "160.0.0.1",
    "170.0.0.1",
    "180.0.0.1",
    "190.0.0.1",
    "200.0.0.1",
    "210.0.0.1",
    "[20::1]",
    "[30::1]",
    "[40::1]",
    "[50::1]",
    "[60::1]",
    "[70::1]",
    "[80::1]",
    "[90::1]",
    "[100::1]",
    "[110::1]",
    "[120::1]",
    "[130::1]",
    "[140::1]",
    "[150::1]",
    "[160::1]",
    "[170::1]",
    "[180::1]",
    "[190::1]",
    "[200::1]",
    "[210::1]",
    "testonlyad777777777777777777777777777777777777777775b6qd.onion",
    "testonlyah77777777777777777777777777777777777777777z7ayd.onion",
    "testonlyal77777777777777777777777777777777777777777vp6qd.onion",
    "testonlyap77777777777777777777777777777777777777777r5qad.onion",
    "testonlyat77777777777777777777777777777777777777777udsid.onion",
    "testonlyax77777777777777777777777777777777777777777yciid.onion",
    "testonlya777777777777777777777777777777777777777777rhgyd.onion",
    "testonlybd77777777777777777777777777777777777777777rs4ad.onion",
    "testonlybp77777777777777777777777777777777777777777zs2ad.onion",
    "testonlybt777777777777777777777777777777777777777777x6id.onion",
    "testonlybx777777777777777777777777777777777777777775styd.onion",
    "testonlyb3777777777777777777777777777777777777777774ckid.onion",
    "testonlycd77777777777777777777777777777777777777777733id.onion",
    "testonlych77777777777777777777777777777777777777777t6kid.onion",
    "testonlycl77777777777777777777777777777777777777777tt3ad.onion",
    "testonlyct77777777777777777777777777777777777777777wvhyd.onion",
    "testonlycx7777777777777777777777777777777777777777774bad.onion",
    "testonlyc377777777777777777777777777777777777777777u6aid.onion",
    "testonlydd777777777777777777777777777777777777777777u5ad.onion",
    "testonlydh77777777777777777777777777777777777777777wgnyd.onion",
    "testonlyad77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyah77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyap77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyat77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyax77777777777777777777777777777777777777777q.b32.i2p",
    "testonlya377777777777777777777777777777777777777777q.b32.i2p",
    "testonlya777777777777777777777777777777777777777777q.b32.i2p",
    "testonlybd77777777777777777777777777777777777777777q.b32.i2p",
    "testonlybh77777777777777777777777777777777777777777q.b32.i2p",
    "testonlybl77777777777777777777777777777777777777777q.b32.i2p",
    "testonlybp77777777777777777777777777777777777777777q.b32.i2p",
    "testonlybt77777777777777777777777777777777777777777q.b32.i2p",
    "testonlybx77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyb777777777777777777777777777777777777777777q.b32.i2p",
    "testonlych77777777777777777777777777777777777777777q.b32.i2p",
    "testonlycp77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyct77777777777777777777777777777777777777777q.b32.i2p",
    "testonlycx77777777777777777777777777777777777777777q.b32.i2p",
    "testonlyc377777777777777777777777777777777777777777q.b32.i2p",
    "testonlyc777777777777777777777777777777777777777777q.b32.i2p",
    "[fc00::1]",
    "[fc00::2]",
    "[fc00::3]",
    "[fc00::5]",
    "[fc00::6]",
    "[fc00::7]",
    "[fc00::8]",
    "[fc00::9]",
    "[fc00::10]",
    "[fc00::11]",
    "[fc00::12]",
    "[fc00::13]",
    "[fc00::15]",
    "[fc00::16]",
    "[fc00::17]",
    "[fc00::18]",
    "[fc00::19]",
    "[fc00::20]",
    "[fc00::22]",
    "[fc00::23]",
)


class _Destination:
    """A peer the proxy forwards one connection to: Core's `P2PInterface`.

    A `Listener`, accepting once and read on a thread of its own, as
    Core's `start_p2p_listener` leaves a listener to its network thread.
    `tx_store` is Core's `P2PDataStore`'s own, answering a `getdata` for
    what it holds; `data_store` marks the one destination Core makes a
    `P2PDataStore`. `relay` is the flag its own `version` sends.
    `message_count` and `last_message` are the accepted `Peer`'s own.
    """

    def __init__(self, *, data_store: bool = False, relay: bool = True) -> None:
        self.data_store = data_store
        self.tx_store: dict[bytes, Tx] = {}
        self._relay = relay
        self._peer: Peer | None = None
        self._sending = threading.Lock()
        self._closing = threading.Event()
        self.connected = threading.Event()
        self.disconnected = threading.Event()
        self._listener = Listener(_MAGIC)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    @property
    def address(self) -> tuple[str, int]:
        """Return the `(host, port)` the proxy forwards to."""
        return self._listener.address

    @property
    def message_count(self) -> Counter[str]:
        """Return the count of each command received, none before a peer."""
        return Counter() if self._peer is None else self._peer.message_count

    @property
    def last_message(self) -> dict[str, Message]:
        """Return the latest message of each command received."""
        return {} if self._peer is None else self._peer.last_message

    def send(self, payload: Payload) -> None:
        """Send `payload`, one sender at a time.

        :raises RuntimeError: no connection has arrived.
        """
        if self._peer is None:
            err_msg = "no connection to send on"
            raise RuntimeError(err_msg)
        with self._sending:
            self._peer.send(payload)

    def wait_for_disconnect(self) -> None:
        """Core's own `wait_for_disconnect`, over `disconnected`."""
        assert self.disconnected.wait(scaled(_WAIT))

    def close(self) -> None:
        """Stop listening, close the connection, and join the thread."""
        self._closing.set()
        self._listener.close()
        if self._peer is not None:
            self._peer.close()
        self._thread.join(scaled(_WAIT))

    def _run(self) -> None:
        """Accept the connection, then answer it until it closes."""
        try:
            with self._listener:
                peer = self._listener.accept()
        except OSError:
            return
        self._peer = peer
        if self._closing.is_set():
            peer.close()
        self.connected.set()
        try:
            while True:
                try:
                    message = peer.receive()
                except TimeoutError:
                    continue
                self._answer(message)
        except OSError:
            pass
        finally:
            self.disconnected.set()

    def _answer(self, message: Message) -> None:
        """Core's `P2PInterface`'s own `on_*`, and `P2PDataStore.on_getdata`."""
        if message.command == "version":
            version = Version.parse(message.payload)
            self.send(
                Version(
                    services=_P2P_SERVICES,
                    user_agent=_USER_AGENT,
                    nonce=secrets.randbelow(2**64),
                    relay=self._relay,
                )
            )
            if version.version >= _WTXID_RELAY_VERSION:
                self.send(WtxidRelay())
            self.send(Verack())
        elif message.command == "ping":
            self.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            wanted = [i for i in items if i.type_code != InventoryType.UNDEFINED]
            if wanted:
                self.send(GetData(wanted))
        elif message.command == "getdata":
            for item in GetData.parse(message.payload).items:
                tx = self.tx_store.get(item.hash)
                if item.type_code in _TX_TYPES and tx is not None:
                    self.send(TxPayload(tx, include_witness=True))


@dataclass
class _Redirect:
    """One entry of Core's own `destinations`: a type, and where it went.

    `node` is `None` for the connection forwarded to the second node.
    """

    conn_type: str
    node: _Destination | None


class _Destinations:
    """Core's own `destinations_factory`, and what it keeps.

    `originator` is the node whose `getpeerinfo` names each connection's
    type, and `receiver` the `(host, port)` the first private broadcast
    connection is forwarded to, both set once the nodes are built.
    """

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.destinations: list[_Redirect] = []
        self.trigger_no_relay_peer = False
        self.no_relay_peer: _Destination | None = None
        self.originator: NodeAdapter | None = None
        self.receiver: tuple[str, int] = ("", 0)

    def factory(self, request: Socks5Request, proxy_client: str) -> tuple[str, int]:
        """Forward the first private broadcast connection to the second node.

        The first outbound full-relay one goes to a store, the one a step
        asks for to a peer relaying nothing, and every other to a
        `_Destination` of its own. `proxy_client` is what the node's own
        `getpeerinfo` reports as the connection's `addrbind`.

        :raises TimeoutError: the node never listed the connection.
        """
        originator = self.originator
        assert originator is not None
        conn_type = None

        def connection_type_found() -> bool:
            nonlocal conn_type
            for peer in originator.rpc.call("getpeerinfo"):
                if peer.get("addrbind") == proxy_client:
                    conn_type = peer["connection_type"]
                    return True
            return False

        wait_until(connection_type_found, timeout=_WAIT)

        with self.lock:
            i = len(self.destinations)
            listener = None
            if conn_type == "private-broadcast" and not any(
                d.conn_type == "private-broadcast" for d in self.destinations
            ):
                address = self.receiver
            else:
                if conn_type == "outbound-full-relay" and not any(
                    d.conn_type == "outbound-full-relay" for d in self.destinations
                ):
                    listener = _Destination(data_store=True)
                elif conn_type == "private-broadcast" and self.trigger_no_relay_peer:
                    listener = _Destination(relay=False)
                    self.trigger_no_relay_peer = False
                    self.no_relay_peer = listener
                else:
                    listener = _Destination()
                address = listener.address
            self.destinations.append(_Redirect(str(conn_type), listener))
            assert len(self.destinations) == i + 1
            return address

    def no_relay(self) -> _Destination | None:
        """Return the peer sending `relay` off, once the factory made it."""
        with self.lock:
            return self.no_relay_peer

    def close(self) -> None:
        """Close every destination made."""
        with self.lock:
            nodes = [d.node for d in self.destinations if d.node is not None]
        for node in nodes:
            node.close()


def _node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    datadir: Path,
    extra_args: list[str],
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Build a node over `datadir`, started with `extra_args` by default."""
    rpc_port, p2p_port = free_ports(2)
    return make_adapter(cls, executable, datadir, rpc_port, p2p_port, extra_args)


def _debug_log(
    node: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> Path:
    """Return the log Core's own lines are read from, or skip.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def _newer(node: NodeAdapter) -> bool:
    """Whether `node` answers past `_PRIVATE_BROADCAST_RPCS_VERSION`.

    Core's own claim for every node, bitcoind older than the constant
    excepted, read off its own `getnetworkinfo` `version`.
    """
    if not isinstance(node, BitcoindAdapter):
        return True
    version = node.rpc.call("getnetworkinfo")["version"]
    return bool(version >= _PRIVATE_BROADCAST_RPCS_VERSION)


def _raw(tx: Tx) -> str:
    """Return `tx`'s own hex, witness included, for `sendrawtransaction`."""
    return tx.serialize(True, check_validity=False).hex()


def _assert_rpc_error(
    node: NodeAdapter, code: int, message: str, method: str, params: list[object]
) -> None:
    """Core's `assert_raises_rpc_error`: the code, and the message within."""
    with pytest.raises(RpcError, match=re.escape(message)) as refusal:
        node.rpc.call(method, params)
    assert refusal.value.code == code


def _wait_for_tx(peer: Peer, tx: Tx) -> None:
    """Core's `wait_for_tx`, answering a `ping` and an `inv` meanwhile.

    :raises TimeoutError: `tx` never arrived within Core's own wait.
    """
    deadline = time.monotonic() + scaled(_WAIT)
    while time.monotonic() < deadline:
        message = peer.receive(timeout=deadline - time.monotonic())
        if message.command == "ping":
            peer.send(Pong(Ping.parse(message.payload).nonce))
        elif message.command == "inv":
            items = Inv.parse(message.payload).items
            wanted = [i for i in items if i.type_code != InventoryType.UNDEFINED]
            if wanted:
                peer.send(GetData(wanted))
        elif (
            message.command == "tx" and TxPayload.parse(message.payload).tx.id == tx.id
        ):
            return
    err_msg = f"never saw tx {tx.id.hex()} within the wait"
    raise TimeoutError(err_msg)


def malleated_to_invalid_witness(tx: Tx) -> Tx:
    """Core's `malleate_tx_to_invalid_witness` (`test_framework/messages.py`).

    The first input's witness replaced by garbage, which keeps the txid
    and moves the wtxid.
    """
    bad = Tx(
        version=tx.version,
        lock_time=tx.lock_time,
        vin=[replace(tx.vin[0], script_witness=Witness([b"garbage"])), *tx.vin[1:]],
        vout=list(tx.vout),
        check_validity=False,
    )
    assert bad.id == tx.id
    assert bad.hash != tx.hash
    return bad


def _has_version(peer: _Destination) -> bool:
    """Whether `peer` received the one `version`, Core's own wait on it."""
    return peer.message_count["version"] == 1


def _as_core_reads(address: NetworkAddress) -> tuple[int, bytes, int]:
    """Return `address` as Core's `CAddress.deserialize` reads a `version`'s.

    The services, the last four octets of the address, which Core reads
    as IPv4 whatever the twelve before them hold, and the port.
    """
    return address.services, address.ip.packed[-4:], address.port


def _check_broadcasts(
    proxied: _Destinations,
    tx_originator: NodeAdapter,
    tx: Tx,
    broadcasts_to_expect: int,
    skip_destinations: int,
) -> None:
    """Core's own `check_broadcasts`: the next private broadcasts of `tx`.

    Every destination past `skip_destinations` is read in turn until
    `broadcasts_to_expect` of them were private broadcasts of `tx`; then
    `getprivatebroadcastinfo` must list `tx`, each peer it went to, and at
    least that many of them having received it.
    """

    def wait_and_get_destination(n: int) -> _Redirect:
        def get_destinations_len() -> int:
            with proxied.lock:
                return len(proxied.destinations)

        wait_until(lambda: get_destinations_len() > n, timeout=_WAIT)
        with proxied.lock:
            return proxied.destinations[n]

    broadcasts_done = 0
    i = skip_destinations - 1
    while broadcasts_done < broadcasts_to_expect:
        i += 1
        peer = wait_and_get_destination(i).node
        if peer is None:
            # the first private broadcast connection, to the second node
            continue
        wait_until(partial(_has_version, peer), timeout=_WAIT)
        version = Version.parse(peer.last_message["version"].payload)
        if version.services != ServiceFlags.NODE_NONE:
            # not a private broadcast: a feeler, or a block-relay-only one
            continue
        peer.wait_for_disconnect()
        assert dict(peer.message_count) == {
            "version": 1,
            "verack": 1,
            "inv": 1,
            "tx": 1,
            "ping": 1,
        }
        dummy_address = _as_core_reads(NetworkAddress(ServiceFlags.NODE_NONE))
        assert version.version == _P2P_PRIVATE_VERSION
        assert version.services == ServiceFlags.NODE_NONE
        assert version.timestamp == 0
        assert _as_core_reads(version.addr_recv) == dummy_address
        assert _as_core_reads(version.addr_from) == dummy_address
        assert version.user_agent == _PRIVATE_USER_AGENT
        assert version.start_height == 0
        assert not version.relay
        received = TxPayload.parse(peer.last_message["tx"].payload).tx
        assert received.id == tx.id
        broadcasts_done += 1

    pbinfo = tx_originator.rpc.call("getprivatebroadcastinfo")
    pending = [
        t
        for t in pbinfo["transactions"]
        if t["txid"] == tx.id.hex() and t["wtxid"] == tx.hash.hex()
    ]
    assert len(pending) == 1
    assert pending[0]["hex"].lower() == _raw(tx).lower()
    peers = pending[0]["peers"]
    assert len(peers) >= _NUM_PRIVATE_BROADCAST_PER_TX
    if _newer(tx_originator):
        attempts = _MAX_PRIVATE_BROADCAST_ATTEMPTS - len(peers)
        assert pending[0]["attempts_remaining"] == attempts
    else:
        assert "attempts_remaining" not in pending[0]
    assert all("address" in p and "sent" in p for p in peers)
    assert sum(1 for p in peers if "received" in p) >= broadcasts_to_expect


def _refused_without_private_broadcast(node: NodeAdapter) -> None:
    """Core's first step, `node` running without `-privatebroadcast`.

    `getprivatebroadcastinfo` and `abortprivatebroadcast` refused, or on a
    build before `_PRIVATE_BROADCAST_RPCS_VERSION`, no transaction listed
    and none to abort.
    """
    if _newer(node):
        _assert_rpc_error(node, -32601, _NOT_ENABLED, "getprivatebroadcastinfo", [])
        _assert_rpc_error(
            node, -32601, _NOT_ENABLED, "abortprivatebroadcast", ["00" * 32]
        )
    else:
        assert node.rpc.call("getprivatebroadcastinfo") == {"transactions": []}
        _assert_rpc_error(
            node,
            -5,
            "Transaction not in private broadcast queue",
            "abortprivatebroadcast",
            ["00" * 32],
        )


def _fill_node_addrman(node: NodeAdapter) -> None:
    """Core's own `fill_node_addrman`, over `_ADDRESSES`.

    An address `addpeeraddress` does not add is passed over, as Core's
    logs it and goes on.
    """
    for address in _ADDRESSES:
        port = 0 if address.endswith(".i2p") else 8333
        node.rpc.call("addpeeraddress", [address, port, False])


def _tx_returner_and_other(proxied: _Destinations) -> tuple[_Destination, _Destination]:
    """Return the first outbound full-relay destination and the second.

    Core's own `set_tx_returner_and_other`, waited on: the first is the
    store, and the second a plain peer.
    """
    found: list[_Destination] = []

    def set_tx_returner_and_other() -> bool:
        found.clear()
        with proxied.lock:
            for dest in proxied.destinations:
                if dest.conn_type == "outbound-full-relay" and dest.node is not None:
                    assert dest.node.data_store == (not found)
                    found.append(dest.node)
                    if len(found) == 2:
                        return True
        return False

    wait_until(set_tx_returner_and_other, timeout=_WAIT)
    return found[0], found[1]


def _share_chain(source: NodeAdapter, target: NodeAdapter) -> None:
    """Hand `target` every block `source` holds, over `submitblock`."""
    for height in range(1, source.rpc.call("getblockcount") + 1):
        block_hash = source.rpc.call("getblockhash", [height])
        block = source.rpc.call("getblock", [block_hash, 0])
        assert target.rpc.call("submitblock", [block]) is None


def transactions_are_broadcast_privately(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Core's `run_test`, in its order, but for its last step.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the nodes' own data directories go.
    :param skip_counts: the session's own tally.
    """
    proxied = _Destinations()
    with ExitStack() as stack:
        socks5_server = stack.enter_context(
            Socks5Proxy(authentication=True, destinations_factory=proxied.factory)
        )
        stack.callback(proxied.close)
        tx_originator = _node(
            make_adapter,
            cls,
            executable,
            tmp_path / "node0",
            [
                "-cjdnsreachable",
                "-v2transport=0",
                "-test=addrman",
                "-privatebroadcast",
                f"-proxy={socks5_server.endpoint}",
                "-i2psam=127.0.0.1:1",
                "-dnsseed=0",
                "-peertimeout=999999999",
            ],
        )
        tx_receiver = _node(
            make_adapter,
            cls,
            executable,
            tmp_path / "node1",
            ["-connect=0", "-peertimeout=999999999"],
        )
        for capability in (
            Capability.PRIVATE_BROADCAST,
            Capability.PROXY,
            Capability.CJDNS,
            Capability.I2P_SAM,
            Capability.V2TRANSPORT,
            Capability.PEER_TIMEOUT,
            Capability.KNOWN_ADDRESSES,
            Capability.MINE,
            Capability.CLOCK,
        ):
            require(capability, tx_originator.capabilities, skip_counts)
        log_path = _debug_log(tx_originator, skip_counts)
        proxied.originator = tx_originator
        proxied.receiver = tx_receiver.p2p_address
        stack.callback(tx_originator.stop)
        stack.callback(tx_receiver.stop)
        tx_originator.start()
        tx_receiver.start()

        # Core's cached chain: a mature coin for each spend, on both nodes
        wallet = MiniWallet(tx_originator)
        wallet.generate(COINBASE_MATURITY + _COINS_SPENT - 1)
        _share_chain(tx_originator, tx_receiver)

        far_observer = stack.enter_context(Peer(tx_receiver.p2p_address, _MAGIC))
        far_observer.handshake()
        far_observer.sync_with_ping()

        _refused_without_private_broadcast(tx_receiver)
        _fill_node_addrman(tx_originator)

        txs = wallet.create_self_transfer_chain(chain_length=3)
        tx_originator.rpc.call("sendrawtransaction", [_raw(txs[0]), 0.1])

        # first private broadcast: the recipient receives it, and relays it
        wait_until(
            lambda: len(tx_receiver.rpc.call("getrawmempool")) > 0, timeout=_WAIT
        )
        _wait_for_tx(far_observer, txs[0])

        # one already checked above, the others now
        _check_broadcasts(
            proxied, tx_originator, txs[0], _NUM_PRIVATE_BROADCAST_PER_TX - 1, 0
        )

        # the same transaction again, not in the mempool yet
        ignoring_msg = (
            "Ignoring unnecessary request to schedule an already scheduled "
            f"transaction: txid={txs[0].id.hex()}, wtxid={txs[0].hash.hex()}"
        )
        with assert_debug_log(log_path, [ignoring_msg], timeout=_WAIT):
            tx_originator.rpc.call("sendrawtransaction", [_raw(txs[0]), 0])

        # a malleated transaction with an invalid witness
        malleated_invalid = malleated_to_invalid_witness(txs[0])
        _assert_rpc_error(
            tx_originator,
            -26,
            "mempool-script-verify-flag-failed",
            "sendrawtransaction",
            [_raw(malleated_invalid), 0.1],
        )

        # the transaction is not in the originator's own mempool
        assert len(tx_originator.rpc.call("getrawmempool")) == 0

        inv = Inventory(InventoryType.MSG_WTX, txs[0].hash)
        tx_returner, other_peer = _tx_returner_and_other(proxied)
        assert tx_returner.connected.wait(scaled(_WAIT))
        assert other_peer.connected.wait(scaled(_WAIT))

        # an inv, and the node's getdata for it
        tx_returner.tx_store[txs[0].hash] = txs[0]
        assert "getdata" not in tx_returner.last_message
        received_back_msg = (
            "Received our privately broadcast transaction "
            f"(txid={txs[0].id.hex()}) from the network"
        )
        with assert_debug_log(log_path, [received_back_msg], timeout=0):
            tx_returner.send(Inv([inv]))
            returner = tx_returner
            wait_until(lambda: "getdata" in returner.last_message, timeout=_WAIT)
            wait_until(
                lambda: len(tx_originator.rpc.call("getrawmempool")) > 0,
                timeout=_WAIT,
            )

        # the normal broadcast to another peer
        other = other_peer

        def inv_arrived() -> bool:
            last = other.last_message.get("inv")
            if last is None:
                return False
            first = Inv.parse(last.payload).items[0]
            return first.type_code == inv.type_code and first.hash == inv.hash

        wait_until(inv_arrived, timeout=_WAIT)

        # getprivatebroadcastinfo no longer lists it, received back
        pbinfo = tx_originator.rpc.call("getprivatebroadcastinfo")
        pending = [
            t
            for t in pbinfo["transactions"]
            if t["txid"] == txs[0].id.hex() and t["wtxid"] == txs[0].hash.hex()
        ]
        assert len(pending) == 0

        # a transaction already in the mempool
        skip_destinations = len(proxied.destinations)
        tx_originator.rpc.call("sendrawtransaction", [_raw(txs[0]), 0])
        _check_broadcasts(
            proxied,
            tx_originator,
            txs[0],
            _NUM_PRIVATE_BROADCAST_PER_TX,
            skip_destinations,
        )

        # a transaction with a dependency in the mempool
        skip_destinations = len(proxied.destinations)
        tx_originator.rpc.call("sendrawtransaction", [_raw(txs[1]), 0.1])
        _check_broadcasts(
            proxied,
            tx_originator,
            txs[1],
            _NUM_PRIVATE_BROADCAST_PER_TX,
            skip_destinations,
        )

        # a transaction with a dependency not in the mempool, refused
        assert len(tx_originator.rpc.call("getrawmempool")) == 1
        for maxfeerate in (0.1, 0):
            _assert_rpc_error(
                tx_originator,
                -25,
                "bad-txns-inputs-missingorspent",
                "sendrawtransaction",
                [_raw(txs[2]), maxfeerate],
            )

        # txs[1] was not received back, so a clock past the longest
        # `NextTxBroadcast` (`net_processing.cpp`) sends it again
        delta = 20 * 60
        skip_destinations = len(proxied.destinations)
        rebroadcast_msg = f"Reattempting broadcast of stale txid={txs[1].id.hex()}"
        with assert_debug_log(log_path, [rebroadcast_msg], timeout=_WAIT):
            tx_originator.set_mock_time(int(time.time()) + delta)
            tx_originator.rpc.call("mockscheduler", [delta])
        _check_broadcasts(proxied, tx_originator, txs[1], 1, skip_destinations)
        tx_originator.set_mock_time(0)

        # a pair with one txid and two valid wtxids
        unmodified = wallet.create_self_transfer()
        parent_amount = unmodified.vout[0].value - 10000
        child_amount = parent_amount - 10000
        siblings_parent, sibling1, sibling2 = malleated_package(
            unmodified, parent_amount, child_amount
        )
        assert sibling1.id == sibling2.id
        assert sibling1.hash != sibling2.hash
        assert len(tx_originator.rpc.call("getrawmempool")) == 1
        tx_returner.send(TxPayload(siblings_parent, include_witness=True))
        wait_until(
            lambda: len(tx_originator.rpc.call("getrawmempool")) > 1, timeout=_WAIT
        )
        tx_originator.rpc.call("sendrawtransaction", [_raw(sibling1), 0.1])
        tx_originator.rpc.call("sendrawtransaction", [_raw(sibling2), 0.1])

        # abortprivatebroadcast removes a pending transaction
        tx_abort = wallet.create_self_transfer()
        tx_originator.rpc.call("sendrawtransaction", [_raw(tx_abort), 0.1])
        listed = tx_originator.rpc.call("getprivatebroadcastinfo")["transactions"]
        assert tx_abort.hash.hex() in [t["wtxid"] for t in listed]
        abort_res = tx_originator.rpc.call("abortprivatebroadcast", [tx_abort.id.hex()])
        assert len(abort_res["removed_transactions"]) == 1
        assert abort_res["removed_transactions"][0]["txid"] == tx_abort.id.hex()
        assert abort_res["removed_transactions"][0]["wtxid"] == tx_abort.hash.hex()
        removed_hex = abort_res["removed_transactions"][0]["hex"]
        assert removed_hex.lower() == _raw(tx_abort).lower()
        listed = tx_originator.rpc.call("getprivatebroadcastinfo")["transactions"]
        assert all(t["wtxid"] != tx_abort.hash.hex() for t in listed)

        # abortprivatebroadcast refuses a transaction it does not hold
        _assert_rpc_error(
            tx_originator,
            -5,
            "Transaction not in private broadcast queue",
            "abortprivatebroadcast",
            ["0" * 64],
        )

        # a private broadcast destination signaling relay=false is dropped
        tx_no_relay = wallet.create_self_transfer()
        disconnect_msg = (
            "Disconnecting: does not support transaction relay (connected in vain)"
        )
        with assert_debug_log(log_path, [disconnect_msg], timeout=0):
            with proxied.lock:
                proxied.no_relay_peer = None
                proxied.trigger_no_relay_peer = True
            tx_originator.rpc.call("sendrawtransaction", [_raw(tx_no_relay), 0.1])
            wait_until(lambda: proxied.no_relay() is not None, timeout=_WAIT)
            no_relay_peer = proxied.no_relay()
            assert no_relay_peer is not None
            wait_until(partial(_has_version, no_relay_peer), timeout=_WAIT)
            no_relay_peer.wait_for_disconnect()
        assert dict(no_relay_peer.message_count) == {"version": 1}
