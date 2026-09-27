# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`: the oracle, bitcoind on any chain it runs.

The release is `31.1`, fetched from bitcoincore.org and verified against
its published sha256, the same one
[btclib's `integration-bitcoind.yml`](https://github.com/btclib-org/btclib/blob/main/.github/workflows/integration-bitcoind.yml)
pins -- a build of `master` is a later issue of its own
([ISS 2220](https://github.com/btclib-org/btclib/issues/2220)'s step 5).
This module holds none of that fetch: it is handed the daemon's own path,
already installed -- `btclib-org/.github`'s `install_bitcoind.py` is what
installs it in CI, and `tests/integration/conftest.py` is what hands it
over.
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
    "BitcoindAdapter",
]

# the wallet `mine` pays to, loaded from the datadir where a restart or
# an earlier adapter left it there, created where nothing did
_MINER_WALLET = "miner"

# the subdirectory of `-datadir` each chain writes its cookie and its
# `debug.log` into, the main chain writing into `-datadir` itself:
# `CreateBaseChainParams` (`src/chainparamsbase.cpp`), whose signet entry
# is `signet` for the default signet a command line with no
# `-signetchallenge` runs
_CHAIN_DIRS = {
    "main": "",
    "test": "testnet3",
    "testnet4": "testnet4",
    "signet": "signet",
    "regtest": "regtest",
}

# the capabilities a node on any chain but regtest lacks: `generatetoaddress`
# and `generateblock` give up after `maxtries` nonces (`src/rpc/mining.cpp`),
# a bound regtest's own target is met within and another chain's is not in
# practice;
# `setmocktime` refuses a chain that is not `IsMockableChain`
# (`src/rpc/node.cpp`), and so does `addconnection` (`src/rpc/net.cpp`);
# `-testactivationheight` is read by `ReadRegTestArgs`
# (`src/chainparams.cpp`) alone; and `AppInitParameterInteraction`
# (`src/init.cpp`) refuses `-test` on any other chain
_REGTEST_ONLY = frozenset(
    {
        Capability.MINE,
        Capability.CLOCK,
        Capability.TEST_ACTIVATION_HEIGHT,
        Capability.TYPED_OUTBOUND,
        Capability.REINDEX_AFTER_FAILURE,
        Capability.GENERATE,
    }
)

# the capabilities a node on the main chain lacks: `-acceptnonstdtxn` is
# refused on a chain that is not `IsTestChain` (`src/node/mempool_args.cpp`)
_TEST_CHAIN_ONLY = frozenset({Capability.ACCEPT_NON_STANDARD})

# the capabilities a build without wallet support lacks, `_has_wallet`
# being what says so: `mine` pays a wallet's own address, and
# `NODE_WALLET` is the wallet itself
_WALLET_ONLY = frozenset({Capability.MINE, Capability.NODE_WALLET})


@lru_cache
def _has_wallet(executable: str) -> bool:
    """Return whether `executable` was built with wallet support.

    A Core build tree's own `test/config.ini` records this under
    `[components] ENABLE_WALLET` (`capability.py`'s own module docstring
    is the rule this reads), but that file sits beside a build tree's own
    binary -- `<build>/test/config.ini` beside `<build>/bin/bitcoind` --
    and nowhere near a release tarball's: `bitcoind-31.1`'s own layout,
    this repository's pinned oracle, has no `test/` directory at all.
    `-help`'s own output is what every `bitcoind`, built or fetched,
    answers alike: `common/args.cpp`'s `ArgsManager::GetHelpMessage`
    prints a "Wallet options:" group only where some argument was
    registered under `OptionsCategory::WALLET`, which `wallet/init.cpp`'s
    `WalletInit::AddWalletOptions` does and `dummywallet.cpp`'s own
    `DummyWalletInit::AddWalletOptions` does not -- that implementation
    hides every wallet argument with `AddHiddenArgs` instead, so a build
    without wallet support still starts on `-disablewallet` but never
    mentions it in `-help` (measured against Core's `master`). A probe of
    the binary itself, in the same standing as `btclib_node.py`'s own
    `_writes_auth_cookie`: no port bound, no data directory created, and
    cached per executable because the answer is a fact about the build
    rather than about any one adapter instance.

    `ENABLE_WALLET` is the one `[components]` entry a capability
    `BitcoindAdapter` declares rests on
    ([ISS 53](https://github.com/btclib-org/bitcoin-node-tests/issues/53)).
    `ENABLE_ZMQ`, `ENABLE_EXTERNAL_SIGNER`, `ENABLE_EMBEDDED_ASMAP` and
    `ENABLE_USDT_TRACEPOINTS` gate nothing a `Capability` member names --
    `-zmqpub*` and `getzmqnotifications`, `-signer` and
    `enumeratesigners`, a bare `-asmap` and `exportasmap`'s own answer,
    and tracepoints among what they do gate; each remaining entry of Core's
    `test/config.ini.in` names executables the build produced,
    `ENABLE_IPC`'s `bitcoin-node` among them, `bitcoind` itself never
    listening on `-ipcbind` (measured against Core's `master`). So for
    what this adapter declares, this probe answers everything the file
    would, and answers for a release too. A capability that comes to
    rest on a second entry is probed the same way, off the binary: the
    file would be a second source for the fact, and one a release cannot
    consult.

    `-nosettings` is not optional: `-help` alone still runs enough of
    `AppInit` to read and rewrite the *default* datadir's own
    `settings.json` -- unrelated to `-datadir`, which nothing here has
    passed yet -- and two probes racing on that file print "Settings
    file could not be written" in place of the help text, `Wallet
    options:` included, rather than refusing to start. Measured live
    under twenty concurrent probes of the pinned `31.1` release, with
    `-nosettings` absent: two answered `_has_wallet` `False` for a binary
    that has one -- `xdist`'s own several workers each constructing a
    `BitcoindAdapter` is exactly that concurrency.

    :param executable: the `bitcoind` binary to probe.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-help", "-nosettings"], check=False, capture_output=True
    )
    return b"\nWallet options:" in probe.stdout


class BitcoindAdapter(NodeAdapter):
    """A `bitcoind`: cookie authentication, and every capability.

    RPC authenticates by cookie, the file `-datadir` writes once the
    node is listening -- rule 1's "how RPC authenticates", answered by a
    file rather than a credential this adapter invents.

    `Capability.MINE` is `generatetoaddress` over a wallet this adapter
    loads or creates on use, and it is not a fact fixed for the whole
    class: `mine` needs a build with wallet support compiled in, which
    every release this repository fetches has, but a Core developer's own
    build tree can configure out
    (`cmake -DENABLE_WALLET=OFF`, or `--disable-wallet` under autotools)
    -- ISS 35's own rule (`capability.py`'s module docstring), a fact
    read from the running build rather than assumed for the whole class.
    `_has_wallet` above is the probe, and `__init__` below is what drops
    the capability from an instance built against a `bitcoind` lacking
    it, rather than declaring it and failing `mine`'s own wallet calls
    once a test actually calls it.
    `Capability.NODE_WALLET` is bitcoind's own built-in wallet, dropped by
    the same probe (`_WALLET_ONLY`): `_command` passes no
    `-disablewallet`, so a build with wallet support serves every wallet
    RPC. This adapter adds no method for it. A test creates the wallets
    it names and reaches each through `self.rpc.for_wallet(name)`,
    `bitcoin_core_rpc`'s own client for `/wallet/<name>`, which keeps this
    client's credential and transport, `--tracerpc` included. It names
    the wallet on every call, never the node's own endpoint: once `mine`
    has loaded `_MINER_WALLET` beside a test's own, bitcoind refuses a
    wallet method there that names no wallet (`RPC_WALLET_NOT_SPECIFIED`,
    `src/wallet/rpc/util.cpp`).
    `Capability.CONNECT` is `node.connect_nodes`
    (`node.py`), unconditional here since bitcoind answers `addnode` and
    `getnetworkinfo` the way every Core-compatible node does.
    `Capability.DISCONNECT` is `node.disconnect_nodes`'s own
    `disconnectnode`, and `Capability.BAN` is `setban`/`listbanned`/
    `clearbanned`: all three, like `addnode`, are in this release's own
    `help` listing with no argument, unconditional the same way
    (measured against the pinned `31.1`, [ISS bitcoin-node-tests#43](https://github.com/btclib-org/bitcoin-node-tests/issues/43)).
    `Capability.RAW_MESSAGE` is `sendmsgtopeer`, a debug RPC this release
    answers (measured against the pinned `31.1`: not in `help`'s own
    listing, which is for discoverability rather than availability, but
    `help sendmsgtopeer` answers its own signature) and which no other
    adapter's node offers yet. `Capability.BLK_FILES` is unconditional
    too: this is Core's own binary, so `blk*.dat` under `blocks/` is the
    format it already writes, not one this adapter has to add anything
    for. `Capability.DEBUG_LOG` is `debug_log_path` below, over the
    node's own `-debug=net`, `-debug=addrman`, `-debug=txreconciliation`
    and `-debug=reindex`: bitcoind's own binary is what writes Core's own
    wording, which is the fact this capability names.
    `Capability.UA_COMMENT` is unconditional too: `-uacomment` is Core's
    own flag, so this is the one node under test that always has it,
    whatever a later option capability turns out to name.
    `Capability.CLOCK` is `setmocktime`, wrapped by
    `NodeAdapter.set_mock_time` (`node.py`) -- a regtest-only RPC in the
    same standing as `sendmsgtopeer` above (measured against the pinned
    `31.1`: also absent from `help`'s own listing, and also answering
    `help setmocktime` directly). `Capability.RPC_AUTH_CONFIG` is
    unconditional too: `rpcauth`, `rpcwhitelist` and
    `rpcwhitelistdefault` are this binary's own `bitcoin.conf` keys,
    read the same way regardless of which adapter wrote the file.
    `Capability.RPC_AUTH_NEGATION` is unconditional too: `-norpcauth`
    disabling every `-rpcauth` given before it is `ArgsManager`'s own
    generic negation of a list-type setting, not a fact `-rpcauth`
    itself carries -- measured live against the pinned `31.1`, a request
    authenticated with a credential named on the command line before
    `-norpcauth` gets 401 once the node has started.
    `Capability.TEST_ACTIVATION_HEIGHT` is unconditional too:
    `-testactivationheight` is a debug-only flag of this binary's own,
    read by `ArgsManager` before any deployment is checked, so nothing
    about which deployment or which height is named changes whether the
    flag itself is recognised.
    `Capability.V2TRANSPORT` is unconditional too: `-v2transport` is
    this binary's own flag, defaulting to `1` on the pinned `31.1`
    (measured against `-help`'s own listing) -- node-to-node connections
    already report `transport_protocol_type: v2` in `getpeerinfo` with
    no argument at all, and `-v2transport=0` on either side falls back to
    `v1`. This is a fact about a connection between two adapters of this
    kind, not about a `Peer` (`peer.py`): that class speaks only the
    plaintext v1 wire format, so a `Peer` reaches this node over v1
    regardless of `-v2transport`, BIP324's own detection accepting a v1
    handshake from either side.
    `Capability.DATACARRIER`, `Capability.PERMIT_BARE_MULTISIG`,
    `Capability.DUST_RELAY_FEE`, `Capability.BYTES_PER_SIGOP`,
    `Capability.LIMIT_CLUSTER_COUNT`, `Capability.LIMIT_CLUSTER_SIZE` and
    `Capability.MAXMEMPOOL` are unconditional too: `-datacarrier`,
    `-datacarriersize`, `-permitbaremultisig`, `-dustrelayfee`,
    `-bytespersigop`, `-limitclustercount`, `-limitclustersize` and
    `-maxmempool` are all ordinary mempool/relay-policy flags of this
    binary's own, recognised regardless of what a caller sets them to
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)).
    `Capability.DESCRIPTOR_ACTIVITY` and `Capability.BLOCK_STATS` are
    unconditional too: `getdescriptoractivity` and `getblockstats` are
    both RPCs of this binary's own, answered regardless of which
    descriptor, block or statistic a caller names.
    `Capability.FASTPRUNE`, `Capability.INBOUND_EVICTION` and
    `Capability.BLOCK_FILTER_INDEX` are unconditional too: `-fastprune`,
    `-maxconnections` and `-blockfilterindex` are this binary's own flags,
    and inbound eviction and `scanblocks` are its own behaviour behind
    the second and the third.
    `Capability.VALIDATE_ADDRESS` is unconditional too: `validateaddress`
    is this binary's own RPC (`src/rpc/output_script.cpp`), with no
    wallet behind it.
    `Capability.TYPED_OUTBOUND` is `addconnection`, wrapped by
    `NodeAdapter.add_outbound_connection` (`node.py`): a regtest-only RPC
    in the same standing as `setmocktime` above (measured against the
    pinned `31.1`: absent from `help`'s own listing, answering
    `help addconnection` directly).
    `Capability.RPC_WORK_QUEUE` is unconditional too: `-rpcthreads` and
    `-rpcworkqueue` are this binary's own flags, and the refusal of a
    request past the queue's bound is its own HTTP server's
    (`src/httpserver.cpp`).
    `Capability.BLOCKS_ONLY` and `Capability.BLOCK_FROM_PEER` are
    unconditional too: `-blocksonly` is this binary's own flag, and
    `getblockfrompeer` its own RPC (`src/rpc/blockchain.cpp`).
    `Capability.ACCEPT_NON_STANDARD` is `-acceptnonstdtxn`, this binary's
    own debug-only flag, which it refuses on main alone.
    `Capability.SUSPEND_NETWORK` is unconditional: `setnetworkactive`
    is this binary's own RPC (`src/rpc/net.cpp`).
    `Capability.DESCRIPTOR_INFO` is unconditional too: `getdescriptorinfo`
    is this binary's own RPC (`src/rpc/output_script.cpp`), with no
    wallet behind it.
    `Capability.PEER_TIMEOUT` and `Capability.MEMPOOL_EXPIRY` are
    unconditional too: `-peertimeout` and `-mempoolexpiry` are this
    binary's own flags (`src/init.cpp`).
    `Capability.SIGN_RAW_TRANSACTION` is unconditional:
    `signrawtransactionwithkey` and `combinerawtransaction` are this
    binary's own RPCs (`src/rpc/rawtransaction.cpp`), with no wallet
    behind them.
    `Capability.INVALIDATE_BLOCK` is unconditional too: `invalidateblock` is
    this binary's own RPC (`src/rpc/blockchain.cpp`), and so is
    `scantxoutset`, `Capability.SCAN_UTXO_SET`'s.
    `Capability.GENERATE` is `generatetoaddress` and `generateblock`
    (`src/rpc/mining.cpp`), which need no wallet, unlike `mine`'s own
    `generatetoaddress` over one: it is declared on regtest alone, not
    narrowed by `_has_wallet`.
    `Capability.REINDEX_AFTER_FAILURE` is `-test`'s own
    `reindex_after_failure_noninteractive_yes`, a debug-only flag of this
    binary's own (`src/init.cpp`), which it refuses off regtest.
    `Capability.PROXY`, `Capability.CJDNS`, `Capability.I2P_SAM` and
    `Capability.ONLYNET` are unconditional too: `-proxy`, `-onion`,
    `-proxyrandomize`, `-cjdnsreachable`, `-i2psam`, `-i2pacceptincoming`
    and `-onlynet` are this binary's own flags (`src/init.cpp`).
    `Capability.TX_RECONCILIATION` and `Capability.PEER_BLOOM_FILTERS` are
    unconditional: `-txreconciliation` and `-peerbloomfilters` are
    this binary's own flags (`src/init.cpp`).
    `Capability.REINDEX` is unconditional: `-reindex` and
    `-reindex-chainstate` are this binary's own flags (`src/init.cpp`).
    `Capability.CAPTURE_MESSAGES` and `Capability.BLOCKS_XOR` are
    unconditional: `-capturemessages` and `-blocksxor` are this binary's
    own flags (`src/init.cpp`).
    `Capability.ORPHANAGE` is unconditional too: `getorphantxs` is this
    binary's own RPC (`src/rpc/mempool.cpp`), hidden from `help`'s own
    listing and answered on every chain.

    Every chain the release runs is in `chains`. On any chain but regtest
    an instance drops `_REGTEST_ONLY`'s capabilities, which only regtest
    answers, and on main `_TEST_CHAIN_ONLY`'s too.
    """

    capabilities: AbstractSet[Capability] = frozenset(
        {
            Capability.MINE,
            Capability.CONNECT,
            Capability.DISCONNECT,
            Capability.BAN,
            Capability.RAW_MESSAGE,
            Capability.BLK_FILES,
            Capability.DEBUG_LOG,
            Capability.UA_COMMENT,
            Capability.CLOCK,
            Capability.RPC_AUTH_CONFIG,
            Capability.RPC_AUTH_NEGATION,
            Capability.TEST_ACTIVATION_HEIGHT,
            Capability.V2TRANSPORT,
            Capability.DATACARRIER,
            Capability.PERMIT_BARE_MULTISIG,
            Capability.DUST_RELAY_FEE,
            Capability.BYTES_PER_SIGOP,
            Capability.LIMIT_CLUSTER_COUNT,
            Capability.LIMIT_CLUSTER_SIZE,
            Capability.MAXMEMPOOL,
            Capability.DESCRIPTOR_ACTIVITY,
            Capability.BLOCK_STATS,
            Capability.FASTPRUNE,
            Capability.INBOUND_EVICTION,
            Capability.BLOCK_FILTER_INDEX,
            Capability.VALIDATE_ADDRESS,
            Capability.TYPED_OUTBOUND,
            Capability.RPC_WORK_QUEUE,
            Capability.BLOCKS_ONLY,
            Capability.BLOCK_FROM_PEER,
            Capability.ACCEPT_NON_STANDARD,
            Capability.SUSPEND_NETWORK,
            Capability.DESCRIPTOR_INFO,
            Capability.PEER_TIMEOUT,
            Capability.MEMPOOL_EXPIRY,
            Capability.SIGN_RAW_TRANSACTION,
            Capability.INVALIDATE_BLOCK,
            Capability.REINDEX_AFTER_FAILURE,
            Capability.GENERATE,
            Capability.SCAN_UTXO_SET,
            Capability.PROXY,
            Capability.CJDNS,
            Capability.I2P_SAM,
            Capability.ONLYNET,
            Capability.NODE_WALLET,
            Capability.TX_RECONCILIATION,
            Capability.PEER_BLOOM_FILTERS,
            Capability.REINDEX,
            Capability.CAPTURE_MESSAGES,
            Capability.BLOCKS_XOR,
            Capability.ORPHANAGE,
        }
    )
    chains: AbstractSet[str] = frozenset(_CHAIN_DIRS)

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
        """Construct the adapter, then drop what the build or the chain lacks.

        `super().__init__` runs first, the same ordering
        `BtclibNodeAdapter.__init__` (`btclib_node.py`) uses and for the
        same reason: `_check_extra_args(self._command(), extra_args)`
        needs `self._executable` set before `_command` can be called.
        `_has_wallet` is then this class's own per-build probe, read once
        per instance rather than once per `mine` call,
        `_REGTEST_ONLY` is what any other `chain` drops, and
        `_TEST_CHAIN_ONLY` what main drops besides.
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
        if not _has_wallet(executable):
            self.capabilities = self.capabilities - _WALLET_ONLY
        if chain != "regtest":
            self.capabilities = self.capabilities - _REGTEST_ONLY
        if chain == "main":
            self.capabilities = self.capabilities - _TEST_CHAIN_ONLY

    @override
    def _command(self) -> list[str]:
        """Return bitcoind's own argv, a loopback-only, ephemeral node.

        `-natpmp=0`, `-discover=0` and `-listenonion=0`: `-bind` already
        names the one address this node listens on regardless of
        `-listen`'s own default, so nothing here needs to reach a
        gateway, a public address lookup or a Tor control port -- a
        throwaway node run from a test suite wants none of the
        three. `-fallbackfee` is set because a chain with no fee history
        refuses to fund a transaction without it, which `Capability.MINE`
        meets the moment a caller spends what it mines. `-debug=net`,
        `-debug=addrman`, `-debug=txreconciliation` and `-debug=reindex`
        are `Capability.DEBUG_LOG`'s own condition: the log lines the log
        family's tests read are `LogDebug`'s (`src/util/log.h`), in Core's
        own `net`, `addrman`, `txreconciliation` and `reindex` categories,
        and print at all only where their own category is enabled.
        `-debug` accumulates, each occurrence enabling one more category,
        so each is an entry of its own rather than one replacing another --
        unconditional here rather than left to a per-test option, since
        `_check_extra_args` (`node.py`) refuses an `extra_args` entry
        naming `-debug` once this argv sets it.

        `-unsafesqlitesync` is Core's own `write_config` (`util.py`) line,
        written there "so that the tests don't timeout": it turns a
        wallet's SQLite `synchronous` pragma off (`src/wallet/sqlite.cpp`),
        so a block a loaded wallet connects waits on no flush to disk.
        Without it, one `generatetoaddress` over a loaded wallet spent most
        of its time in those flushes and outlasted the RPC client's own
        timeout on a loaded machine (measured against the pinned `31.1`,
        [ISS 226](https://github.com/btclib-org/bitcoin-node-tests/issues/226)).
        A build without wallet support starts on it too:
        `DummyWalletInit::AddWalletOptions` (`src/dummywallet.cpp`) hides it
        rather than leaving it unknown.

        `-rpcallowip=127.0.0.1` is what makes `-rpcbind` bind at all:
        Core's `HTTPBindAddresses` (`src/httpserver.cpp`) ignores
        `-rpcbind` unless `-rpcallowip` is also given, binds `::1` and
        `127.0.0.1` instead, and starts where either one binds. With both
        given, `127.0.0.1` is the one RPC endpoint, so a port another
        process already holds there fails init and the process exits,
        which `_wait_for_rpc` (`node.py`) reports on its exit code rather
        than waiting out its timeout against a node answering on `::1`
        alone (measured against the pinned `31.1`,
        [ISS 135](https://github.com/btclib-org/bitcoin-node-tests/issues/135)).
        It admits no client the default does not: `InitHTTPAllowList`
        admits `127.0.0.0/8` and `::1` whatever `-rpcallowip` names.
        Core's own framework passes neither option (`util.py`'s
        `write_config`), its ports coming from `--portseed` (`util.py`'s
        `p2p_port`) rather than from the OS, as `free_ports` (`node.py`)
        takes them. `-bind` needs no such partner: `CConnman::InitBinds`
        (`src/net.cpp`) fails init on any `-bind` address it cannot bind.

        `-chain` names the chain. On any chain but regtest, `-connect=0`,
        `-dnsseed=0` and `-fixedseeds=0` keep the node off the real
        network: no outbound connection is drawn, and no DNS or fixed seed
        is asked for one. Regtest's seed, `dummySeed.invalid.`, resolves
        nowhere, so a regtest node reaches it only through a proxy, and a
        test giving the node one passes `-dnsseed=0` itself
        [ISS 205](https://github.com/btclib-org/bitcoin-node-tests/issues/205).
        Core's own `write_config` (`util.py`) writes all three on every chain,
        `connect=0` unless a test passes `disable_autoconnect=False`.
        `-connect=0` would turn listening off by default, but
        `InitParameterInteraction` (`src/init.cpp`) reads `-bind` first
        and keeps listening on the address it names.
        """
        isolation = (
            []
            if self._chain == "regtest"
            else ["-connect=0", "-dnsseed=0", "-fixedseeds=0"]
        )
        return [
            self._executable,
            f"-chain={self._chain}",
            f"-datadir={self._datadir}",
            f"-rpcport={self._rpc_port}",
            "-rpcbind=127.0.0.1",
            "-rpcallowip=127.0.0.1",
            f"-bind=127.0.0.1:{self._p2p_port}",
            "-natpmp=0",
            "-discover=0",
            "-listenonion=0",
            "-fallbackfee=0.0002",
            "-printtoconsole=0",
            "-unsafesqlitesync",
            "-debug=net",
            "-debug=addrman",
            "-debug=txreconciliation",
            "-debug=reindex",
            *isolation,
        ]

    @property
    def _chain_dir(self) -> Path:
        """Return the directory of this node's cookie and log: `_CHAIN_DIRS`."""
        return self._datadir / _CHAIN_DIRS[self._chain]

    @override
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a client authenticating the way this node was configured.

        The cookie `-datadir` writes, unless `rpc_auth` (`NodeAdapter.__init__`)
        names a credential instead: a node started with `-rpcuser`/
        `-rpcpassword` or `-norpccookiefile` (`extra_args`) writes no
        cookie at all, so nothing here can wait on a file that never
        appears -- the caller that put either flag on the command line is
        the one that already knows the credential to authenticate with.
        `self._trace_rpc` (`--tracerpc`) wraps whichever transport that
        choice builds in `traced_transport`'s own print, credential or
        cookie alike.
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
        cookie_path = self._chain_dir / ".cookie"
        return BitcoinCoreRpcClient(url, cookie_path=cookie_path, transport=transport)

    @property
    def debug_log_path(self) -> Path:
        """Return this node's own `debug.log`, `Capability.DEBUG_LOG`'s fact.

        `debug.log` in `_chain_dir`, the directory the cookie file above
        is read from -- bitcoind's own convention, not a name this adapter
        invents.
        """
        return self._chain_dir / "debug.log"

    @override
    def _log_path(self) -> Path:
        """Return `debug_log_path`, for `start`'s own `TimeoutError`."""
        return self.debug_log_path

    def _load_miner_wallet(self) -> None:
        """Make `_MINER_WALLET` loaded: already, loaded from disk, or created.

        Asked of the node on every call rather than cached per adapter: a
        restart leaves the wallet on disk and unloaded, and a second adapter
        over the same datadir finds the first one's there, where
        `createwallet` answers "Database already exists" (measured against
        the pinned `31.1`, [ISS 86](https://github.com/btclib-org/bitcoin-node-tests/issues/86)).
        `listwalletdir` is what names a wallet on disk and unloaded.
        """
        loaded = self.rpc.call("listwallets")
        if isinstance(loaded, list) and _MINER_WALLET in loaded:
            return
        walletdir = self.rpc.call("listwalletdir")
        on_disk = walletdir.get("wallets", []) if isinstance(walletdir, dict) else []
        names = {entry.get("name") for entry in on_disk if isinstance(entry, dict)}
        method = "loadwallet" if _MINER_WALLET in names else "createwallet"
        self.rpc.call(method, [_MINER_WALLET])

    def mine(self, count: int = 1) -> list[str]:
        """Mine `count` blocks to this adapter's wallet, return their hashes.

        `generatetoaddress`, over the wallet `_load_miner_wallet` makes
        loaded first: Core's own regtest mining needs an address to pay,
        and a wallet answers `getnewaddress` with one that this same
        client can later spend from, which is `Capability.MINE`'s whole
        promise rather than only a taller chain.

        :param count: how many blocks to mine.
        :returns: the mined blocks' own hashes, Core's own
            `generatetoaddress` return value.
        """
        self._load_miner_wallet()
        wallet_rpc = self.rpc.for_wallet(_MINER_WALLET)
        address = wallet_rpc.call("getnewaddress")
        hashes = self.rpc.call("generatetoaddress", [count, address])
        if not isinstance(hashes, list):
            err_msg = f"generatetoaddress answered {hashes!r}, not a list of hashes"
            raise TypeError(err_msg)
        return hashes
