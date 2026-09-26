# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`: the first target, `btclib-node` over `python -m`.

[btclib-node PR 1012](https://github.com/btclib-org/btclib-node/pull/1012)
is what this adapter needs already served: `getblock`, `submitblock`,
`addnode` and `getnetworkinfo`, measured present in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table before this
module was written.

`Capability.MINE` is not declared, and this is the finding rather than a
gap this adapter papers over: a solo `btclib-node`, with no peer, never
leaves `NodeStatus.SyncingHeaders` (`src/btclib_node/__init__.py`'s own
`run`), and `main.update_chain`'s own `_ready_fork` refuses to connect
anything -- a block this adapter submits included -- while `node.status`
sits below `HeaderSynced`. Measured at `btclib-node` `382a29fb`:
`submitblock` answers `None` (accepted) and stores the block, and
`getblockcount`/`getbestblockhash` never move; a second node peered to
the first over `addnode` can itself receive and connect that same block
over ordinary p2p relay, so the gap is the solo node's own status latch
and not the block or the RPC. Filed as
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071).

Independently,
[ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)
is what makes `p2p_getdata` itself fail here: `block_db` never holds the
genesis block, so neither `getblock` nor a p2p `getdata` can serve the
one block a fresh regtest node -- mined or not -- starts at.

`Capability.BLK_FILES` is not declared either, and is not a gap this
adapter is waiting on: `block_db.BlockDB` is its own on-disk format, not
Core's `blk*.dat`, by the decision
[ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)
already made and closed on -- reading Core's own files was refused in
favour of `-connect`/`-addnode` delivering the same blocks over loopback
p2p, which this repository's own `Capability.CONNECT` already reaches.

`Capability.DISCONNECT` is not declared, on either build: `addnode` is
answered (this module's own opening paragraph) but `disconnectnode`
names no callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` (`422d2640`) and at `main`
(`d98bd7d6`) alike. Filed as
[ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193).

`Capability.BAN` is not declared either, on either build: `setban`,
`listbanned` and `clearbanned` name no callback in the same dispatch
table, measured at the same two revisions --
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088)
already tracks it, filed independently of this adapter.

`Capability.UA_COMMENT` is not declared: measured against `cli.py`'s
own `_build_parser` at `btclib-node` `18b6ae1e`, `-uacomment` is not
one of its registered flags.

`Capability.CLOCK` is not declared: `setmocktime` names no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at
`btclib-node` `18b6ae1e2c74`.

`Capability.RPC_AUTH_CONFIG` is not a class-level fact the way the four
above are, and unlike them this is not a fact about `btclib-node`
itself: `cli.py`'s own `_RECOGNIZED_KEYS` at `18b6ae1e2c74` already names
`rpcauth`, `rpcwhitelist` and `rpcwhitelistdefault`, landed by
[ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
alongside the cookie authentication `_writes_auth_cookie` above already
probes for -- so it is a fact about which build the executable an
instance is constructed with names, and `__init__` below declares it on
that instance by riding on the same probe rather than by a second one:
a build whose `btclib_node.rpc.auth` imports (`_writes_auth_cookie`
returns `True`) also recognises those three keys, both having landed in
the same commit. The class-level `capabilities` stays
`frozenset({Capability.CONNECT})`, the fact true of every build; an
instance built with an executable carrying `rpc.auth` gains
`Capability.RPC_AUTH_CONFIG` on top of it. PyPI's `2026.9.24` release,
what this repository's own `TF2_BTCLIB_NODE_PYTHON` names, predates that
issue -- measured live to warn `ignoring unknown configuration value
rpcauth` and start anyway rather than to enforce it -- so an instance
built against it does not gain the capability; one built against a
`main` carrying #1070 does.

`Capability.RPC_AUTH_NEGATION` is never declared, on either build:
`cli.py`'s own module docstring states this module has no generic
negation, registering `-nolisten` and `-norpccookiefile` by hand as the
two negated spellings it recognises -- `-norpcauth` is not a third, so
it is refused as an unrecognised argument (the released build) or as an
"Invalid parameter" (`main`, whose own `_parse_args` added that wording
for a flag-shaped token no registered option names) rather than accepted
and clearing every `-rpcauth` given before it. Filed as
[ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176).

`Capability.V2TRANSPORT` is never declared: `cli.py`'s own
`_build_parser` names no `-v2transport` flag at all, measured at
`btclib-node` `18b6ae1e2c74`, and `rpc/callbacks.py`'s own `addnode`
reads a `v2transport` parameter only to discard it -- "`v2transport` is
read and type-checked, matching Core's own optional third argument, and
otherwise unused: BIP324 is not a transport this node speaks yet" is
that module's own wording -- so there is no BIP324 codec behind either
spelling for this capability to name.

`Capability.INBOUND_EVICTION` is declared per instance too, by
`_evicts_inbound`'s own probe: a build carrying
`btclib_node.p2p.eviction`, a port of Core's `SelectNodeToEvict`
landed by
[ISS btclib-node#1064](https://github.com/btclib-org/btclib-node/issues/1064),
disconnects an unprotected inbound peer once its inbound slots are full,
and registers `-maxconnections` to bound them. PyPI's `2026.9.24`
release carries neither, so an instance built against it does not gain
the capability.

`Capability.DESCRIPTOR_ACTIVITY` and `Capability.BLOCK_STATS` are never
declared, on either build: neither `getdescriptoractivity` nor
`getblockstats` names a callback in `src/btclib_node/rpc/callbacks.py`'s
own dispatch table, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`d7693b2f5a16`) alike.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient
from bitcoin_core_rpc.transport import urlopen_transport

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter, traced_transport

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "BtclibNodeAdapter",
]

# btclib-node's own build before ISS btclib-node#1070 (`422d2640`, what
# PyPI's `2026.9.24` release installs) checks no credential at all
# and binds RPC to 127.0.0.1 only -- ISS 2135's own census, quoted in ISS
# 2220 -- so a placeholder is what `bitcoin_core_rpc.BitcoinCoreRpcClient`
# is given for that build instead of one the constructor refuses to be
# built with none of: `_writes_auth_cookie` below is what decides whether
# it is used at all, rather than the cookie every later build writes.
_RPC_USER = "tf2"
_RPC_PASSWORD = "tf2"  # noqa: S105 -- ignored by a pre-#1070 build; see above


@lru_cache
def _writes_auth_cookie(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node writes an RPC cookie.

    ISS btclib-node#1070 (`18b6ae1e`) landed Core-style RPC authentication
    -- `-rpcuser`/`-rpcpassword`, the cookie `rpc/auth.py`'s own
    `RpcAuth.start` writes to `<data_dir>/regtest/.cookie` unless one of
    them is given, and `-rpcwhitelist` -- and gained the module
    `btclib_node.rpc.auth` along with it, absent from every build before.
    Its presence is what this checks, matching the probe
    `tests/integration/conftest.py`'s own `btclib_node_python` fixture
    already makes for the package itself. A build before it (`382a29fb`)
    checks no credential at all and answers unrecognised any
    `-rpcuser`/`-rpcpassword` given on its own argv -- confirmed live,
    exit `2` there before the node's RPC ever starts.

    A probe of the interpreter/version pair, never of a running node: no
    port is bound and no data directory is created. Cached per
    `executable`, because the answer is a fact about the install rather
    than about any one adapter instance, and `_rpc_client` below is
    called fresh on every access to `.rpc`.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", "import btclib_node.rpc.auth"],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


@lru_cache
def _evicts_inbound(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node evicts inbound peers.

    `import btclib_node.p2p.eviction` exiting zero, in the standing of
    `_writes_auth_cookie` above: no port bound, no data directory
    created, and cached per executable.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", "import btclib_node.p2p.eviction"],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


class BtclibNodeAdapter(NodeAdapter):
    """A regtest `btclib-node`, run as `python -m btclib_node`.

    Not the console script `pip install btclib-node` also provides:
    `cli.py`'s own module docstring is where the reason not to run that
    entry point directly from a spawning process is argued --
    `ReimportedMainProcessError` reaching every path but the one
    `python -m` and its own `__main__.py` exempt.
    """

    capabilities: AbstractSet[Capability] = frozenset({Capability.CONNECT})

    @override
    def __init__(
        self,
        executable: str,
        datadir: Path,
        rpc_port: int,
        p2p_port: int,
        extra_args: Sequence[str] = (),
        rpc_auth: tuple[str, str] | None = None,
        *,
        trace_rpc: bool = False,
    ) -> None:
        """Construct the adapter, then add each probed capability that holds.

        `super().__init__` runs first -- `NodeAdapter.__init__`'s own
        `_check_extra_args(self._command(), extra_args)` needs
        `self._executable` set before `_command` above can be called, and
        that guard is unaffected by which capabilities this instance ends
        up declaring. `_writes_auth_cookie` is then the same probe
        `_rpc_client` below already makes for cookie authentication, not
        a second one: the module docstring's own paragraph on
        `Capability.RPC_AUTH_CONFIG` is why one probe answers both, and
        `_evicts_inbound` answers `Capability.INBOUND_EVICTION`. The
        class-level `capabilities` -- `frozenset({Capability.CONNECT})` --
        is left untouched where both probes answer `False`.
        """
        super().__init__(
            executable,
            datadir,
            rpc_port,
            p2p_port,
            extra_args,
            rpc_auth,
            trace_rpc=trace_rpc,
        )
        probed = set()
        if _writes_auth_cookie(executable):
            probed.add(Capability.RPC_AUTH_CONFIG)
        if _evicts_inbound(executable):
            probed.add(Capability.INBOUND_EVICTION)
        if probed:
            self.capabilities = type(self).capabilities | probed

    @override
    def _command(self) -> list[str]:
        """Return btclib-node's own argv, over `python -m btclib_node`.

        `self._executable` is the interpreter (`sys.executable` of
        whichever environment `btclib-node` is installed into), never
        the console script -- the module docstring is why. Carries no
        `-rpcuser`/`-rpcpassword`: a build before ISS btclib-node#1070
        refuses either flag outright, so the credential is `_rpc_client`
        below's alone, never this argv's.
        """
        return [
            self._executable,
            "-m",
            "btclib_node",
            "-regtest",
            f"-datadir={self._datadir}",
            f"-rpcport={self._rpc_port}",
            "-rpcbind=127.0.0.1",
            f"-port={self._p2p_port}",
        ]

    @override
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a client authenticating the way this build actually checks.

        `rpc_auth` (`NodeAdapter.__init__`) first, where the caller named
        one: a node started with `-rpcuser`/`-rpcpassword` or
        `-norpccookiefile` (`extra_args`) writes no cookie at all, on a
        build past
        [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
        exactly as bitcoind does not either, so nothing here can wait on
        one -- the caller that put either flag on the command line already
        knows the credential to authenticate with instead. Absent that,
        cookie authentication, `BitcoindAdapter`'s own mechanism, where
        `_writes_auth_cookie` finds the build writes one -- the same
        `<datadir>/regtest/.cookie` layout, `chains.RegTest`'s own `name`
        matching bitcoind's `regtest` subdirectory. A build with no
        Core-style RPC authentication at all is given the placeholder
        credential instead, which it never checks. `self._trace_rpc`
        (`--tracerpc`) decides whether either path wraps its transport in
        `traced_transport`'s own print, matching `BitcoindAdapter`.
        """
        url = f"http://127.0.0.1:{self._rpc_port}"
        transport = (
            traced_transport(urlopen_transport)
            if self._trace_rpc
            else urlopen_transport
        )
        if self._rpc_auth is not None:
            user, password = self._rpc_auth
            return BitcoinCoreRpcClient(
                url, user=user, password=password, transport=transport
            )
        if _writes_auth_cookie(self._executable):
            return BitcoinCoreRpcClient(
                url,
                cookie_path=self._datadir / "regtest" / ".cookie",
                transport=transport,
            )
        return BitcoinCoreRpcClient(
            url, user=_RPC_USER, password=_RPC_PASSWORD, transport=transport
        )

    @property
    def log_path(self) -> Path:
        """Return this node's own `history.log`, the disk family's own fact.

        Not `debug_log_path`: `BitcoindAdapter`'s own name is Core's file,
        and this node writes no file of that name. `history.log` is
        `btclib_node`'s own, under the same `<datadir>/regtest/` layout
        the cookie file above reads from -- measured live, at the sha
        this module's own docstring pins.
        """
        return self._datadir / "regtest" / "history.log"
