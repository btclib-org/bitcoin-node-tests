# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`: the first target, `btclib-node` over `python -m`.

[btclib-node PR 1012](https://github.com/btclib-org/btclib-node/pull/1012)
is what this adapter needs already served: `getblock`, `submitblock`,
`addnode` and `getnetworkinfo`, measured present in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table before this
module was written.

`Capability.MINE` is declared per instance, by `_connects_alone`'s
own probe. `mine` below builds and solves each block client-side and
hands it to `submitblock`, and a node with no peer never leaves
`NodeStatus.SyncingHeaders`, so what decides is whether the build's own
`main.update_chain` connects a block at that status: `main` from
btclib-node PR 1152 (`84277406`) on, the fix
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
asked for. Measured at `main` (`35b26d2e`): a solo node accepts the block
and `getblockcount`/`getbestblockhash` move onto it. The released
`2026.9.24` (`422d2640`) answers the same `submitblock` `None` (accepted)
and leaves both at genesis, so an instance built against it does not gain
the capability. Neither build names `generatetoaddress`, `generateblock`
or `getblocktemplate` in `src/btclib_node/rpc/callbacks.py`'s own
dispatch table, which is why `mine` builds the block itself.

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

`Capability.BAN` is declared per instance, by `_serves_ban_list`'s own
probe: a build whose `rpc/callbacks.py` names `setban`, `listbanned` and
`clearbanned` in its public `callbacks`, the table `rpc/main.py` resolves
every request's method through -- `main` from btclib-node PR 1275
(`65510d56`) on, the ban list
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088)
asked for. The released `2026.9.24` (`422d2640`) names none of the three,
so an instance built against it does not gain the capability.

`Capability.UA_COMMENT` is not declared: measured against `cli.py`'s own
`_build_parser` at the released `2026.9.24` (`422d2640`) and its `_OPTIONS`
at `main` (`8ded5494`) alike, `-uacomment` is registered by neither.

`Capability.CLOCK` is not declared: `setmocktime` names no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at
`btclib-node` `18b6ae1e2c74`.

`Capability.RPC_AUTH_CONFIG` is not a class-level fact the way
`BLK_FILES`, `DISCONNECT`, `UA_COMMENT` and `CLOCK` above are, and unlike
them this is not a fact about `btclib-node` itself: `cli.py`'s own
`_RECOGNIZED_KEYS` at `18b6ae1e2c74` already names `rpcauth`,
`rpcwhitelist` and `rpcwhitelistdefault`, landed by
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

`Capability.RPC_AUTH_NEGATION` is declared per instance too, by
`_negates_rpcauth`'s own probe: a build whose `cli.py` reads `-noname` as
`-name` negated, `rpcauth` among its `_OPTIONS`, discards every
`-rpcauth` given before `-norpcauth` -- `main` from btclib-node PR 1165
(`995dd1d0`) on, the behaviour
[ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)
asks for. `_writes_auth_cookie` does not answer it: `995dd1d0`'s parent
`b1184d7c` imports `btclib_node.rpc.auth` and still refuses `-norpcauth`
as an "Invalid parameter". The released `2026.9.24` (`422d2640`) refuses
it as argparse's "unrecognized arguments", `-nolisten` being the one
negated spelling its `_build_parser` registers, so an instance built
against it does not gain the capability.

`Capability.V2TRANSPORT` is never declared: `cli.py`'s own `_build_parser` at
the released `2026.9.24` (`422d2640`) and its `_OPTIONS` at `main` (`8ded5494`)
name no `-v2transport` flag, and `rpc/callbacks.py`'s own `addnode`
reads a `v2transport` parameter only to discard it -- "`v2transport` is read
and type-checked, matching Core's own optional third argument, and otherwise
unused: BIP324 is not a transport this node speaks yet" is that module's own
wording -- so there is no BIP324 codec behind either spelling for this
capability to name.

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
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import NodeAdapter, traced_transport, wait_until

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "BtclibNodeAdapter",
]

# btclib-node's own build before ISS btclib-node#1070 (`422d2640`, what
# PyPI's `2026.9.24` release installs) checks no credential at all
# and binds RPC to 127.0.0.1 only -- ISS btclib-org/btclib#2135's own
# census, quoted in ISS btclib-org/btclib#2220 -- so a placeholder is
# what `bitcoin_core_rpc.BitcoinCoreRpcClient` is given for that build
# instead of one the constructor refuses to be
# built with none of: `_writes_auth_cookie` below is what decides whether
# it is used at all, rather than the cookie every later build writes.
_RPC_USER = "tf2"
_RPC_PASSWORD = "tf2"  # noqa: S105 -- ignored by a pre-#1070 build; see above

# each chain `-chain=` names, in Core's vocabulary, and the subdirectory of
# `-datadir` the node writes its cookie and its log into: `chains.py`'s own
# `name` of the chain `cli.py`'s `_CHAIN_ALIASES` resolves it to, measured at
# the released `2026.9.24` and at `main` (`35b26d2e`) alike. Neither names
# `testnet4`.
_CHAIN_DIRS = {
    "main": "mainnet",
    "test": "testnet",
    "signet": "signet",
    "regtest": "regtest",
}


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


# `tf2` is no `<user>:<salt>$<hash>`, so `RpcAuthEntry.parse` refuses it
# wherever it survives the command line: `build_config` returns only where
# `-norpcauth` discarded it. `-noconf` keeps any `bitcoin.conf` out of it.
_NEGATION_PROBE = (
    "from btclib_node.cli import build_config; "
    'build_config(["-regtest", "-noconf", "-rpcauth=tf2", "-norpcauth"])'
)


@lru_cache
def _negates_rpcauth(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node reads `-norpcauth`.

    Asks the build's own `cli.build_config` -- which reads the command
    line as `main` does, and takes no lock and creates no directory -- to
    read `-rpcauth` followed by its negation, and answers whether it
    returns:
    `_NEGATION_PROBE` above is why returning means the value was
    discarded rather than merely accepted. A build with no generic
    negation refuses the argument and exits nonzero. Otherwise in the
    standing of `_writes_auth_cookie` above: no port bound, and cached
    per executable.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", _NEGATION_PROBE],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


# `update_chain` handed a node still at `SyncingHeaders`: a build that
# gates on the status never reads `chainstate` and exits nonzero, whether
# it returns or trips on the stub further on; a build that does not asks
# `get_first_candidate` first, which exits 0 on the spot.
_SOLO_CONNECT_PROBE = """\
from types import SimpleNamespace
from btclib_node.constants import NodeStatus
from btclib_node.main import update_chain
def reached(): raise SystemExit(0)
index = SimpleNamespace(get_first_candidate=reached)
chainstate = SimpleNamespace(block_index=index)
update_chain(SimpleNamespace(status=NodeStatus.SyncingHeaders, chainstate=chainstate))
raise SystemExit(1)
"""


@lru_cache
def _connects_alone(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node connects with no peer.

    Asks the build's own `main.update_chain`, public in `main`'s own
    `__all__`, whether it looks for a block to connect while
    `node.status` is `SyncingHeaders`, the status a node with no peer
    never leaves: `_SOLO_CONNECT_PROBE` above is how the two answers are
    told apart. Otherwise in the standing of `_writes_auth_cookie` above:
    no node started, no port bound, and cached per executable.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", _SOLO_CONNECT_PROBE],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


# exits 0 only where the dispatch table holds each of `Capability.BAN`'s RPCs
_BAN_PROBE = """\
from btclib_node.rpc.callbacks import callbacks
ban_rpcs = {"setban", "listbanned", "clearbanned"}
raise SystemExit(0 if ban_rpcs <= callbacks.keys() else 1)
"""


@lru_cache
def _serves_ban_list(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node answers the ban RPCs.

    Asks the build's own `rpc.callbacks.callbacks`, public in that
    module's own `__all__`, whether it names `setban`, `listbanned` and
    `clearbanned`: `_BAN_PROBE` above. Otherwise in the standing of
    `_writes_auth_cookie` above: no node started, no port bound, and
    cached per executable.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", _BAN_PROBE],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


class BtclibNodeAdapter(NodeAdapter):
    """A `btclib-node`, run as `python -m btclib_node`.

    Not the console script `pip install btclib-node` also provides:
    `cli.py`'s own module docstring is where the reason not to run that
    entry point directly from a spawning process is argued --
    `ReimportedMainProcessError` reaching every path but the one
    `python -m` and its own `__main__.py` exempt.

    `chains` is every chain `_CHAIN_DIRS` names, `testnet4` not among
    them. On any chain but regtest an instance drops `Capability.MINE`:
    `MiniWallet` builds regtest's own blocks alone.
    """

    capabilities: AbstractSet[Capability] = frozenset({Capability.CONNECT})
    chains: AbstractSet[str] = frozenset(_CHAIN_DIRS)

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
        chain: str = "regtest",
    ) -> None:
        """Construct the adapter, then add each probed capability that holds.

        `super().__init__` runs first -- `NodeAdapter.__init__`'s own
        `_check_extra_args(self._command(), extra_args)` needs
        `self._executable` set before `_command` above can be called, and
        that guard is unaffected by which capabilities this instance ends
        up declaring. `_writes_auth_cookie` is then the same probe
        `_rpc_client` below already makes for cookie authentication, not
        a second one: the module docstring's own paragraph on
        `Capability.RPC_AUTH_CONFIG` is why one probe answers both,
        `_negates_rpcauth` answers `Capability.RPC_AUTH_NEGATION`,
        `_evicts_inbound` answers `Capability.INBOUND_EVICTION`,
        `_connects_alone` answers `Capability.MINE`, and
        `_serves_ban_list` answers `Capability.BAN`. The
        class-level `capabilities` -- `frozenset({Capability.CONNECT})` --
        is left untouched where every probe answers `False`. A `chain`
        other than regtest drops `Capability.MINE` whatever its probe
        answers.
        """
        super().__init__(
            executable,
            datadir,
            rpc_port,
            p2p_port,
            extra_args,
            rpc_auth,
            trace_rpc=trace_rpc,
            chain=chain,
        )
        probed = set()
        if _writes_auth_cookie(executable):
            probed.add(Capability.RPC_AUTH_CONFIG)
        if _negates_rpcauth(executable):
            probed.add(Capability.RPC_AUTH_NEGATION)
        if _evicts_inbound(executable):
            probed.add(Capability.INBOUND_EVICTION)
        if _connects_alone(executable) and chain == "regtest":
            probed.add(Capability.MINE)
        if _serves_ban_list(executable):
            probed.add(Capability.BAN)
        if probed:
            self.capabilities = type(self).capabilities | probed

    def mine(self, count: int = 1) -> list[str]:
        """Mine `count` blocks client-side, return their hashes once connected.

        `MiniWallet.generate` (`mini_wallet.py`) builds, solves and submits
        each block, extending whatever tip the node answers now, and pays
        its coinbase to that class's own anyone-can-spend script: a caller
        that means to spend what it mines holds a `MiniWallet` of its own
        instead. `submitblock` answering `None` says the block was stored,
        not that it became the tip: connecting it is `main.update_chain`'s
        job rather than `rpc/callbacks.py`'s own `submit_block`, so this
        polls `getbestblockhash` until it names the last block, where
        `BitcoindAdapter.mine`'s own `generatetoaddress` answers only once
        connected.

        :param count: how many blocks to mine.
        :returns: the mined blocks' own hashes, oldest first, the shape of
            `BitcoindAdapter.mine`'s own.
        :raises TimeoutError: the node stored the last block and never made
            it its tip.
        """
        hashes = [block_hash.hex() for block_hash in MiniWallet(self).generate(count)]
        if hashes:
            wait_until(lambda: self.rpc.call("getbestblockhash") == hashes[-1])
        return hashes

    @override
    def _command(self) -> list[str]:
        """Return btclib-node's own argv, over `python -m btclib_node`.

        `self._executable` is the interpreter (`sys.executable` of
        whichever environment `btclib-node` is installed into), never
        the console script -- the module docstring is why. Carries no
        `-rpcuser`/`-rpcpassword`: a build before ISS btclib-node#1070
        refuses either flag outright, so the credential is `_rpc_client`
        below's alone, never this argv's.

        `-chain` names the chain. On any chain but regtest, which has no
        seed to reach, `-connect=0` keeps the node from reaching the real
        network: the node's own `P2pManager` asks no DNS or fixed seed and
        draws no outbound connection once `-connect` is given, `0`
        dialling nobody. `-listen=1` keeps the `-port` listener `-connect`
        would turn off by default, the listener every inbound connection a
        test makes dials. That listener binds every interface, on every
        chain, this node having no `-bind` to narrow it
        (ISS btclib-org/btclib-node#1257).
        """
        isolation = [] if self._chain == "regtest" else ["-connect=0", "-listen=1"]
        return [
            self._executable,
            "-m",
            "btclib_node",
            f"-chain={self._chain}",
            f"-datadir={self._datadir}",
            f"-rpcport={self._rpc_port}",
            "-rpcbind=127.0.0.1",
            f"-port={self._p2p_port}",
            *isolation,
        ]

    @property
    def _chain_dir(self) -> Path:
        """Return the directory of this node's cookie and log: `_CHAIN_DIRS`."""
        return self._datadir / _CHAIN_DIRS[self._chain]

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
        `_writes_auth_cookie` finds the build writes one, in `_chain_dir`.
        A build with no
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
                cookie_path=self._chain_dir / ".cookie",
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
        `btclib_node`'s own, in `_chain_dir`, the directory the cookie
        file above is read from.
        """
        return self._chain_dir / "history.log"

    @override
    def _log_path(self) -> Path:
        """Return `log_path`, for `start`'s own `TimeoutError`."""
        return self.log_path
