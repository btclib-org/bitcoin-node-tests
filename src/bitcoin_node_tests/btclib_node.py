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

Independently, [ISS
btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072) is
what makes `p2p_getdata` itself fail on the released build: `block_db` never
holds the genesis block, so neither `getblock` nor a p2p `getdata` can serve
the one block a fresh regtest node -- mined or not -- starts at.

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

`Capability.VALIDATE_ADDRESS` is never declared either: `validateaddress`
names no callback in that same dispatch table, measured at the released
`2026.9.24` (`422d2640`) and at `main` (`d0ead5f0`) alike.

`Capability.TYPED_OUTBOUND` is never declared, on either build:
`addconnection` names no callback in that same dispatch table, measured
at the released `2026.9.24` (`422d2640`) and at `main` (`25776772`)
alike, and `addnode`, the one RPC there that dials, takes Core's own
arguments, none of them a connection type.

`Capability.RPC_WORK_QUEUE` is never declared either: `cli.py` registers
neither `-rpcthreads` nor `-rpcworkqueue`, measured at the released
`2026.9.24` and at `main` (`25776772`) alike.

`Capability.BLOCKS_ONLY` and `Capability.BLOCK_FROM_PEER` are never
declared either: `cli.py` registers no `-blocksonly`, and
`getblockfrompeer` names no callback in that same dispatch table,
measured at the released `2026.9.24` and at `main` (`25776772`) alike.

`Capability.ACCEPT_NON_STANDARD` is never declared either:
`-acceptnonstdtxn` is not among the flags `-help -noconf` prints, measured
at the released `2026.9.24` and at `main` (`19c5661e`) alike.

`Capability.SUSPEND_NETWORK` is never declared either: `setnetworkactive`
names no callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` and at `main` (`19c5661e`)
alike
([ISS btclib-node#1392](https://github.com/btclib-org/btclib-node/issues/1392)).

`Capability.DESCRIPTOR_INFO` is never declared either: `getdescriptorinfo`
names no callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` (`422d2640`) and at `main`
(`4e155386`) alike.

`Capability.PEER_TIMEOUT` and `Capability.MEMPOOL_EXPIRY` are never
declared either: `cli.py` registers neither `-peertimeout` nor
`-mempoolexpiry`, measured at the released `2026.9.24` (`422d2640`) and
at `main` (`4e155386`) alike.

`Capability.SIGN_RAW_TRANSACTION` is never declared either: neither
`signrawtransactionwithkey` nor `combinerawtransaction` names a callback
in `src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at
the released `2026.9.24` (`422d2640`) and at `main` (`4e155386`) alike
([ISS btclib-node#1400](https://github.com/btclib-org/btclib-node/issues/1400)).

`Capability.INVALIDATE_BLOCK` is never declared either: `invalidateblock`
names no callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` and at `main` (`4e155386`)
alike.

`Capability.GENERATE` and `Capability.SCAN_UTXO_SET` are never declared
either: none of `generatetoaddress`, `generateblock`, `help` and
`scantxoutset` names a callback in that same dispatch table, measured at
the released `2026.9.24` (`422d2640`) and at `main` (`d2b4efa5`) alike
([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404),
[ISS btclib-node#1396](https://github.com/btclib-org/btclib-node/issues/1396),
[ISS btclib-node#1405](https://github.com/btclib-org/btclib-node/issues/1405),
[ISS btclib-node#1406](https://github.com/btclib-org/btclib-node/issues/1406)).

`Capability.REINDEX_AFTER_FAILURE` is never declared either: `cli.py`
registers no `-test`, measured at the released `2026.9.24` and at `main`
(`4e155386`) alike, each refusing
`-test=reindex_after_failure_noninteractive_yes` as an unknown argument.

`Capability.PROXY` is never declared either: `cli.py` registers none of
`-proxy`, `-onion` and `-proxyrandomize`, measured against its
`_build_parser` at the released `2026.9.24` (`422d2640`) and its
`_OPTIONS` at `main` (`d2b4efa5`) alike. Nor are `Capability.CJDNS`,
`Capability.I2P_SAM` and `Capability.ONLYNET`: it registers none of
`-cjdnsreachable`, `-i2psam`, `-i2pacceptincoming` and `-onlynet`,
measured the same way at the released `2026.9.24` and at `main`
(`1aeebc67`).

`Capability.NODE_WALLET` is never declared either: `btclib-node` keeps
no wallet, `src/btclib_node/rpc/callbacks.py`'s own dispatch table naming
no wallet RPC -- no `createwallet`, `getnewaddress` or `signmessage` --
measured at the released `2026.9.24` and at `main` (`d2b4efa5`) alike. A
wallet kept beside the node is
[ISS 199](https://github.com/btclib-org/bitcoin-node-tests/issues/199)'s
to reach.

`Capability.TX_RECONCILIATION` and `Capability.PEER_BLOOM_FILTERS` are
never declared either: `cli.py` registers neither `-txreconciliation` nor
`-peerbloomfilters`, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`dca9c2be`) alike, `txreconciliation` being a `-debug`
category at `main`.

`Capability.REINDEX` is never declared either: each build refuses
`-reindex` and `-reindex-chainstate` as unknown arguments, measured at the
released `2026.9.24` and at `main` (`338f64c5`) alike
([ISS btclib-node#1415](https://github.com/btclib-org/btclib-node/issues/1415)).

`Capability.CAPTURE_MESSAGES` and `Capability.BLOCKS_XOR` are never
declared either: `cli.py` registers neither `-capturemessages` nor
`-blocksxor`, measured against its `_build_parser` at the released
`2026.9.24` (`422d2640`) and its `_OPTIONS` at `main` (`98448c4d`) alike.

`Capability.ORPHANAGE` is never declared either: `getorphantxs` names no
callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch table, and
no source file names an orphan, measured at the released `2026.9.24`
(`422d2640`) and at `main` (`1aeebc67`) alike
([ISS btclib-node#1420](https://github.com/btclib-org/btclib-node/issues/1420)).

`Capability.BLOCK_PROPOSAL` is never declared either: `getblocktemplate`
names no callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch
table, measured at the released `2026.9.24` (`422d2640`) and at `main`
(`503edaec`) alike, each answering it `Method not found`
([ISS btclib-node#1427](https://github.com/btclib-org/btclib-node/issues/1427)).

`Capability.ADDRESS_FETCH` is never declared either: `cli.py` registers
no `-seednode`, measured against its `_build_parser` at the released
`2026.9.24` (`422d2640`) and its `_OPTIONS` at `main` (`d4559960`) alike
([ISS btclib-node#1192](https://github.com/btclib-org/btclib-node/issues/1192)).

`Capability.DNS_SEED` is never declared either: `cli.py` registers
neither `-dnsseed` nor `-forcednsseed`, measured against its
`_build_parser` at the released `2026.9.24` (`422d2640`) and its
`_OPTIONS` at `main` (`d4559960`) alike
([ISS btclib-node#1192](https://github.com/btclib-org/btclib-node/issues/1192),
[ISS btclib-node#1265](https://github.com/btclib-org/btclib-node/issues/1265)).
Nor is `Capability.KNOWN_ADDRESSES`: neither `addpeeraddress` nor
`getnodeaddresses` names a callback in `src/btclib_node/rpc/callbacks.py`'s
own dispatch table, measured at the same two commits
([ISS btclib-node#1443](https://github.com/btclib-org/btclib-node/issues/1443)).

`Capability.EXTERNAL_IP` is never declared either: `cli.py` registers no
`-externalip`, measured at the released `2026.9.24` (`422d2640`) and at
`main` (`d4559960`) alike
([ISS btclib-node#1445](https://github.com/btclib-org/btclib-node/issues/1445)).

`Capability.PRIVATE_BROADCAST` is never declared either: `cli.py`
registers no `-privatebroadcast`, and neither `getprivatebroadcastinfo`
nor `abortprivatebroadcast` names a callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at the
released `2026.9.24` (`422d2640`) and at `main` (`d4559960`) alike,
`privatebroadcast` being a `-debug` category at `main`.

`Capability.STARTUP_NOTIFY` is never declared either: `cli.py` registers
no `-startupnotify`, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`d4559960`) alike
([ISS btclib-node#1449](https://github.com/btclib-org/btclib-node/issues/1449)).

`Capability.DUMP_UTXO_SET` is never declared either: no source file
names `dumptxoutset`, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`ecb9b190`) alike
([ISS btclib-node#1471](https://github.com/btclib-org/btclib-node/issues/1471)).

`Capability.LOAD_BLOCK` is never declared either: no source file
names `loadblock`, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`ecb9b190`) alike. Reading Core's block files is left
out by decision, the node taking the same blocks over p2p
([ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)).

`Capability.LISTEN_ADDRESS` is never declared either: `cli.py` registers
`-port` and no `-bind`, and the listener binds `0.0.0.0` and `::` alone,
measured at the released `2026.9.24` (`422d2640`) and at `main`
(`ecb9b190`) alike
([ISS btclib-node#1257](https://github.com/btclib-org/btclib-node/issues/1257)).

`Capability.MAX_TIP_AGE` is never declared either: `cli.py` registers
no `-maxtipage`, the age being `constants.py`'s own `MAX_TIP_AGE` of a
day, measured at the released `2026.9.24` (`422d2640`) and at `main`
(`9ae620c2`) alike
([ISS btclib-node#1474](https://github.com/btclib-org/btclib-node/issues/1474)).

`Capability.PEER_BLOCK_FILTERS` is never declared either: `cli.py`
registers no `-peerblockfilters`, and `p2p/callbacks.py` answers
`getcfilters`, `getcfheaders` and `getcfcheckpt` for every peer while
`p2p/connection.py` signals `NODE_COMPACT_FILTERS` to every one, with no
option to turn either off, measured at the released `2026.9.24`
(`422d2640`) and at `main` (`9ae620c2`) alike
([ISS btclib-node#1395](https://github.com/btclib-org/btclib-node/issues/1395)).

`Capability.RPC_INFO` is never declared either: `getrpcinfo` names no
callback in `src/btclib_node/rpc/callbacks.py`'s own dispatch table,
measured at the released `2026.9.24` (`422d2640`) and at `main`
(`76d7daa4`) alike
([ISS btclib-node#1486](https://github.com/btclib-org/btclib-node/issues/1486)).

`Capability.CLUSTER_LINEARIZATION` is never declared either:
`getmempoolcluster` and `getmempoolfeeratediagram` name no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at the
released `2026.9.24` (`422d2640`) and at `main` (`93c1d066`) alike
([ISS btclib-node#1499](https://github.com/btclib-org/btclib-node/issues/1499)).

`Capability.MINIMUM_CHAIN_WORK` is never declared either: `cli.py`
registers no `-minimumchainwork`, the floor being the chain's own
`minimum_chain_work` (`btclib.consensus`), measured at the released
`2026.9.24` (`422d2640`) and at `main` (`93c1d066`) alike
([ISS btclib-node#1500](https://github.com/btclib-org/btclib-node/issues/1500)).

`Capability.MEMPOOL_GRAPH` is never declared either:
`getmempoolancestors`, `getmempooldescendants` and
`gettxspendingprevout` name no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at the
released `2026.9.24` (`422d2640`) and at `main` (`93c1d066`) alike
([ISS btclib-node#1501](https://github.com/btclib-org/btclib-node/issues/1501)).

`Capability.PACKAGE_ACCEPTANCE` is never declared either: no file under
`src/` names `submitpackage`, measured at the released `2026.9.24`
(`422d2640`) and at `main` (`93c1d066`) alike
([ISS btclib-node#1494](https://github.com/btclib-org/btclib-node/issues/1494)).

`Capability.MIN_RELAY_TX_FEE` is declared per instance, by
`_sets_min_relay_fee`'s own probe: a build whose `cli.py` registers
`-minrelaytxfee` -- `main` from btclib-node PR 1452 (`88f5c894`) on, the
option [ISS btclib-node#1332](https://github.com/btclib-org/btclib-node/issues/1332)
asked for. The released `2026.9.24` (`422d2640`) registers none, its
`Config.min_relay_feerate` taking no flag, so an instance built against
it does not gain the capability.

`Capability.ALERT_NOTIFY` is never declared either: no source file
names `alertnotify`, measured at the released `2026.9.24` (`422d2640`)
and at `main` (`93c1d066`) alike
([ISS btclib-node#1475](https://github.com/btclib-org/btclib-node/issues/1475)).
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.mini_wallet import MiniWallet
from bitcoin_node_tests.node import NodeAdapter, wait_until
from bitcoin_node_tests.timeout_factor import rpc_client_timeout

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
# wherever it survives the command line. Since
# [ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210),
# that refusal is kept on the returned config as `rpc_auth_invalid`
# rather than raised, so `build_config` returns whether or not
# `-norpcauth` discarded the value: the probe below exits on that field
# instead of on the return itself, `getattr` defaulting `False` for a
# build that predates the field and so raises wherever the value
# survives. `-noconf` keeps any `bitcoin.conf` out of it.
_NEGATION_PROBE = (
    "from btclib_node.cli import build_config; "
    'config = build_config(["-regtest", "-noconf", "-rpcauth=tf2", "-norpcauth"]); '
    'raise SystemExit(1 if getattr(config, "rpc_auth_invalid", False) else 0)'
)


@lru_cache
def _negates_rpcauth(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node negates `-rpcauth`.

    Asks the build's own `cli.build_config` -- which reads the command
    line as `main` does, and takes no lock and creates no directory -- to
    read `-rpcauth` followed by its negation, and answers whether the
    resulting config's `rpc_auth_invalid`, where the build has one, is
    false -- and where it has none, whether it returned: `_NEGATION_PROBE`
    above is why exiting zero means the value was discarded rather than
    merely accepted alongside `-norpcauth` on the command line. A build
    with no generic negation refuses the argument and exits nonzero.
    Otherwise in the standing of `_writes_auth_cookie` above: no port
    bound, and cached per executable.

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


# exits 0 only where `-minrelaytxfee`, in Core's BTC/kvB, sets the floor
# `Config.min_relay_feerate` holds in sat/kvB; a build registering no such
# flag refuses it and exits nonzero. `-noconf` keeps any `bitcoin.conf` out
_MIN_RELAY_FEE_PROBE = """\
from btclib_node.cli import build_config
config = build_config(["-regtest", "-noconf", "-minrelaytxfee=0.00000010"])
raise SystemExit(0 if config.min_relay_feerate.sats_per_kvbyte == 10 else 1)
"""


@lru_cache
def _sets_min_relay_fee(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node reads `-minrelaytxfee`.

    Asks the build's own `cli.build_config`, as `_negates_rpcauth` above
    does, to read the flag, and answers whether the resulting config's
    `min_relay_feerate` is the rate it names: `_MIN_RELAY_FEE_PROBE`
    above. Otherwise in the standing of `_writes_auth_cookie` above: no
    node started, no port bound, and cached per executable.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", _MIN_RELAY_FEE_PROBE],
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
        `_connects_alone` answers `Capability.MINE`,
        `_serves_ban_list` answers `Capability.BAN`, and
        `_sets_min_relay_fee` answers `Capability.MIN_RELAY_TX_FEE`. The
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
        if _sets_min_relay_fee(executable):
            probed.add(Capability.MIN_RELAY_TX_FEE)
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
        credential instead, which it never checks. Every path builds its
        client over `NodeAdapter._rpc_transport`, this adapter's own
        connections, `--tracerpc` included, and bounds each call by
        `timeout_factor.rpc_client_timeout`, read when the client is built,
        matching `BitcoindAdapter`.
        """
        url = f"http://127.0.0.1:{self._rpc_port}"
        transport = self._rpc_transport()
        timeout = rpc_client_timeout()
        if self._rpc_auth is not None:
            user, password = self._rpc_auth
            return BitcoinCoreRpcClient(
                url,
                user=user,
                password=password,
                timeout=timeout,
                transport=transport,
            )
        if _writes_auth_cookie(self._executable):
            return BitcoinCoreRpcClient(
                url,
                cookie_path=self._chain_dir / ".cookie",
                timeout=timeout,
                transport=transport,
            )
        return BitcoinCoreRpcClient(
            url,
            user=_RPC_USER,
            password=_RPC_PASSWORD,
            timeout=timeout,
            transport=transport,
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
