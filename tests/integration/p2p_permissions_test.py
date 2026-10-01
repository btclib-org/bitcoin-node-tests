# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_permissions`, as bodies over either node.

Read from Core's `test/functional/p2p_permissions.py` (`fa5f29774872`,
2025-12-16), an option and the wire
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
the permissions `-whitelist` and `-whitebind` grant, read off `getpeerinfo`
(`Capability.PEER_PERMISSIONS`). Each of Core's checks is kept, in its
order:

- a peer holding `forcerelay` has a transaction the node's mempool holds
  already relayed on to a node it is linked to, and a transaction the
  node rejects is not (`Capability.CONNECT`, `Capability.MINE`,
  `Capability.DEBUG_LOG`);
- each `-whitelist` value, alone or with the legacy `-whitelistrelay` and
  `-whitelistforcerelay`, grants exactly the permissions Core's own file
  lists for it;
- a `-whitelist` and a `-whitebind` naming the same peer grant the union
  of both;
- the `in` and `out` directions decide whether a whitelisted address
  grants its permissions to a peer that dials the node or to one the node
  dials, and a bare list grants them to the first only;
- a malformed `-whitelist` or `-whitebind` stops the node starting, with
  Core's own message.

What differs from Core's file:

- the peer whose permissions are read is a `Peer` dialling the node, not
  the second node Core's `connect_nodes(0, 1)` links: a node grants an
  inbound peer permissions by its address and the bind it dials, whatever
  the peer is. The `in` and `out` check keeps both nodes, the side that
  dials being its subject.
- Core replaces its node's `bind=127.0.0.1` with a `whitebind` of the same
  address. The adapter's own `-bind` cannot be replaced (`node.py`'s
  `_check_extra_args`), so `-whitebind` names another port and the peer
  dials that one. The refusal of `-whitebind` beside `-listen=0` has the
  adapter's own `-bind` where Core passes one, and bitcoind's message is
  the same for either (`AppInitParameterInteraction`, `src/init.cpp`).

`p2p_permissions_bitcoind_test.py` and `p2p_permissions_btclib_node_test.py`
run each body, `tests/integration/conftest.py`'s own module docstring
having how.
"""

from __future__ import annotations

import re
from contextlib import nullcontext
from typing import TYPE_CHECKING

import pytest
from btclib.p2p import TxPayload
from btclib.p2p.magic import magic_from_chain
from btclib.tx import Tx, TxOut
from btclib.tx.limits import COINBASE_MATURITY, SEQUENCE_FINAL

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import (
    connect_nodes,
    free_port,
    wait_until,
    wait_until_tips_agree,
)
from bitcoin_node_tests.peer import Peer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractContextManager
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds",
    "a_malformed_permission_list_stops_the_node_starting",
    "a_whitebind_and_a_whitelist_grant_the_union",
    "each_whitelist_grants_the_permissions_it_names",
    "in_and_out_decide_which_connections_a_whitelist_grants",
]

type _Cluster = Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]]

_MAGIC = magic_from_chain("regtest")

# every `(arguments, permissions)` Core's `run_test` hands `checkpermission`
# ahead of its `whitebind` section, in its order
_WHITELISTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    # default permissions (no specific permissions)
    (
        ("-whitelist=127.0.0.1",),
        ("relay", "noban", "mempool", "download"),
    ),
    # no permission (even with forcerelay)
    (("-whitelist=@127.0.0.1", "-whitelistforcerelay=1"), ()),
    # relay permission removed (no specific permissions)
    (
        ("-whitelist=127.0.0.1", "-whitelistrelay=0"),
        ("noban", "mempool", "download"),
    ),
    # forcerelay and relay permission added: the legacy parameter
    # interaction sets whitelistrelay to true where whitelistforcerelay is
    (
        ("-whitelist=127.0.0.1", "-whitelistforcerelay"),
        ("forcerelay", "relay", "noban", "mempool", "download"),
    ),
)

# the same, after Core's `whitebind` section
_MORE_WHITELISTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    # legacy whitelistrelay should be ignored
    (
        ("-whitelist=noban,mempool@127.0.0.1", "-whitelistrelay"),
        ("noban", "mempool", "download"),
    ),
    # legacy whitelistforcerelay should be ignored
    (
        ("-whitelist=noban,mempool@127.0.0.1", "-whitelistforcerelay"),
        ("noban", "mempool", "download"),
    ),
    # missing mempool permission to be considered legacy whitelisted
    (("-whitelist=noban@127.0.0.1",), ("noban", "download")),
    # all permission added
    (
        ("-whitelist=all@127.0.0.1",),
        ("forcerelay", "noban", "mempool", "bloomfilter", "relay", "download", "addr"),
    ),
)

# Core's `assert_start_raises_init_error` calls, each with the text its
# `ErrorMatch.PARTIAL_REGEX` finds in the node's stderr
_REFUSALS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("-whitelist=in,out@127.0.0.1",), "Only direction was set, no permissions"),
    (("-whitelist=oopsie@127.0.0.1",), "Invalid P2P permission"),
    (("-whitelist=noban@127.0.0.1:230",), "Invalid netmask specified in"),
    (("-whitebind=noban@127.0.0.1/10",), "Cannot resolve -whitebind address"),
    (
        ("-whitebind=noban@127.0.0.1", "-listen=0"),
        "Cannot set -bind or -whitebind together with -listen=0",
    ),
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)


def _peers(node: NodeAdapter) -> list[dict[str, object]]:
    """Return `node`'s own `getpeerinfo`."""
    peers = node.rpc.call("getpeerinfo")
    assert isinstance(peers, list)
    return peers


def _debug_log(
    node: BitcoindAdapter | BtclibNodeAdapter, skip_counts: SkipCounts
) -> Path:
    """Return the log a log check reads, or skip where the node keeps none.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    require(Capability.DEBUG_LOG, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def _permissions_of_one_peer(node: NodeAdapter, address: tuple[str, int]) -> list[str]:
    """Dial `node` at `address` and return the permissions it grants the peer.

    The peer is closed on every path.
    """
    with Peer(address, _MAGIC) as peer:
        peer.handshake()
        peer.sync_with_ping()
        (peer_info,) = _peers(node)
        permissions = peer_info["permissions"]
        assert isinstance(permissions, list)
        return [str(permission) for permission in permissions]


def _check_permissions(
    node: NodeAdapter,
    arguments: Sequence[str],
    expected: Sequence[str],
    address: tuple[str, int] | None = None,
) -> None:
    """Core's own `checkpermission`: restart `node`, connect, compare.

    :param node: the node, restarted with `arguments`.
    :param arguments: Core's own `args`.
    :param expected: Core's own `expectedPermissions`; the peer has these
        and no others, in any order.
    :param address: where the peer dials, `node`'s own where `None`.
    """
    node.restart(arguments)
    permissions = _permissions_of_one_peer(node, address or node.p2p_address)
    assert sorted(permissions) == sorted(expected), arguments


def each_whitelist_grants_the_permissions_it_names(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `checkpermission` calls on `-whitelist` alone.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PEER_PERMISSIONS, node.capabilities, skip_counts)
    for arguments, expected in (*_WHITELISTS, *_MORE_WHITELISTS):
        _check_permissions(node, arguments, expected)


def a_whitebind_and_a_whitelist_grant_the_union(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own merge check: a `whitebind` and a `whitelist` together.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PEER_PERMISSIONS, node.capabilities, skip_counts)
    port = free_port()
    # forcerelay should activate relay
    _check_permissions(
        node,
        [
            "-whitelist=noban@127.0.0.1",
            f"-whitebind=bloomfilter,forcerelay@127.0.0.1:{port}",
        ],
        ["noban", "bloomfilter", "forcerelay", "relay", "download"],
        ("127.0.0.1", port),
    )


def in_and_out_decide_which_connections_a_whitelist_grants(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `in` and `out` loop: the node dials, the permissions follow.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.PEER_PERMISSIONS, node0.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    for arguments, expected in (
        (["-whitelist=noban,out@127.0.0.1"], ["noban", "download"]),
        (["-whitelist=noban@127.0.0.1"], []),
    ):
        node0.restart(arguments)
        connect_nodes(node0, node1)
        (peer_info,) = _peers(node0)
        assert peer_info["permissions"] == expected, arguments


def _refusal(node: NodeAdapter, arguments: Sequence[str]) -> str:
    """Start `node` with `arguments`, and return the stderr it exits with.

    Core's own `assert_start_raises_init_error`: the start fails, with an
    exit code other than `0`, before its RPC ever answers.
    """
    with pytest.raises(RuntimeError) as refused:
        node.restart(arguments)
    early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
    assert early_exit is not None
    assert int(early_exit[1]) != 0
    return early_exit[2]


def a_malformed_permission_list_stops_the_node_starting(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `assert_start_raises_init_error` calls on a bad list.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.PEER_PERMISSIONS, node.capabilities, skip_counts)
    node.stop()
    for arguments, message in _REFUSALS:
        assert re.search(message, _refusal(node, arguments)), arguments


def _send_tx_and_test(
    peer: Peer,
    node: NodeAdapter,
    tx: Tx,
    *,
    success: bool,
    expected_log: AbstractContextManager[None],
) -> None:
    """Core's own `send_txs_and_test` for one transaction.

    :param expected_log: the log check the send runs inside.
    """
    with expected_log:
        peer.send(TxPayload(tx, include_witness=True))
        peer.sync_with_ping()
        assert (tx.id.hex() in node.rpc.call("getrawmempool")) is success


def a_forcerelay_peer_has_a_transaction_relayed_that_the_mempool_holds(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's own `check_tx_relay`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    node0, node1 = cluster(2)
    require(Capability.PEER_PERMISSIONS, node1.capabilities, skip_counts)
    require(Capability.CONNECT, node0.capabilities, skip_counts)
    require(Capability.MINE, node0.capabilities, skip_counts)
    log = _debug_log(node1, skip_counts)
    wallet = MiniWallet(node0)
    wallet.generate(COINBASE_MATURITY + 1)
    connect_nodes(node0, node1)
    wait_until_tips_agree([node0, node1])

    node1.restart(["-whitelist=forcerelay@127.0.0.1"])
    with Peer(node1.p2p_address, _MAGIC) as peer:
        peer.handshake()
        peer.sync_with_ping()

        tx = wallet.create_self_transfer(sequence=SEQUENCE_FINAL)
        _send_tx_and_test(peer, node1, tx, success=True, expected_log=nullcontext())

        connect_nodes(node1, node0)
        relayed = f"Force relaying tx {tx.id.hex()} (wtxid={tx.hash.hex()}) from peer=0"
        with assert_debug_log(log, [relayed]):
            _send_tx_and_test(peer, node1, tx, success=True, expected_log=nullcontext())
            wait_until(lambda: tx.id.hex() in node0.rpc.call("getrawmempool"))

        # dust to cause policy rejection but no disconnection, both outputs
        # of no value as Core's aliased `CTxOut` has them
        dust = Tx(
            tx.version,
            tx.lock_time,
            tx.vin,
            [TxOut(0, tx.vout[0].script_pub_key), TxOut(0, tx.vout[0].script_pub_key)],
        )
        # sent twice: the first time it is rejected by the node's policy,
        # the second it is in the filter of recent rejects
        _send_tx_and_test(
            peer,
            node1,
            dust,
            success=False,
            expected_log=assert_debug_log(
                log,
                [
                    f"{dust.id.hex()} (wtxid={dust.hash.hex()}) from peer=0 was not accepted: dust"
                ],
            ),
        )
        _send_tx_and_test(
            peer,
            node1,
            dust,
            success=False,
            expected_log=assert_debug_log(
                log,
                [
                    (
                        f"Not relaying non-mempool transaction {dust.id.hex()} "
                        f"(wtxid={dust.hash.hex()}) from forcerelay peer=0"
                    )
                ],
            ),
        )
