# Changelog

<!-- markdownlint-configure-file
  {
    // MD024/no-duplicate-heading - every release repeats the same few
    // headings, which is what keeps the page readable scrolling down it;
    // only a duplicate under the same release heading would be the
    // accident this rule looks for
    "MD024": { "siblings_only": true }
  }
-->

An entry for anything a reader would notice: what changed, and the issue
it answers. That is section 9 of [the organization standard][std], and it
is narrower than "every change" — a comment reworded inside a workflow
changes nothing a reader of this repository meets, and lands without an
entry. This tree publishes nothing yet, so there is no `RELEASE_NOTES.md`
beside it (section 2 of that standard gives that file to a tier-1 tree).

[std]: https://github.com/btclib-org/.github

Neither this file nor any release notes file this tree gains states how
many entries it holds: a stated number is a line every open branch has
to edit, and this file carries a union merge driver that would keep both
sides' numbers.

## v0 (work in progress, not released yet)

### The repository exists, with the organization's apparatus and the tf2 ledger

Step 2 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220): the
organization's toolchain, lint gate and tests apparatus, plus `TF2.md`
rebuilt with a census script for [ISS btclib-org/btclib#1751][1751].

[1751]: https://github.com/btclib-org/btclib/issues/1751

### A drift line names both commits whole

`check_vendored_vectors.py` prints the pinned commit and upstream's tip as
full shas, in its output and in the tracking issue, so two commits alike in
their first twelve characters print as two (issue btclib-org/.github#1343).

### The adapter: bitcoind first, btclib-node second

A `NodeAdapter` and a `Peer`, and `p2p_getdata` rewritten on both: passes
on bitcoind, fails on btclib-node (issue btclib-org/btclib-node#1072).
(closes #1)

### CONTRIBUTING.md and README.md link GOVERNANCE.md and ROADMAP.md

Both link `GOVERNANCE.md`, how the organization decides, and `ROADMAP.md`, what
it intends to do, one copy of each in btclib-org/.github (issue
btclib-org/.github#1359).

### The first family joins `p2p_getdata`, and a capability for `sendmsgtopeer`

`p2p_block_sync`, `p2p_compactblocks_hb`, `p2p_invalid_locator` and
`p2p_net_deadlock` join `p2p_getdata`, against bitcoind and btclib-node.
(closes #2)

### The disk family's mechanism, and `feature_blocksdir` ported

`NodeAdapter` gains `extra_args`; `Capability.BLK_FILES` names Core's
`blk*.dat` layout, absent from btclib-node by decision (issue
btclib-org/btclib-node#573). `feature_blocksdir` is ported (issue #7).

### The printed skip count sums the whole run, not the controller's own

Each `-n auto` worker hands its own tally to the controller through
`workeroutput`, and the controller folds every one in before printing
the total (closes #16).

### The log family: a wire half and a `Capability.DEBUG_LOG` half

`test_magic_bytes` and `P2PLeakTest`'s obsolete-version check are each
rewritten as a disconnect, passing on both nodes, and a log assertion,
`Capability.DEBUG_LOG`-gated and skipping on btclib-node. (issue #5)

### `NodeAdapter.start` carries a process's own stderr into its `RuntimeError`

Redirected to a file rather than an unread `subprocess.PIPE`, so a
long-running node cannot block on a full pipe buffer, and
`feature_blocksdir`'s refusal half matches each node's own wording (closes #19).

### The option family's mechanism, and `feature_uacomment` ported

`Capability.UA_COMMENT` names Core's `-uacomment`, declared by bitcoind
and absent from btclib-node's own registered flags. `feature_uacomment`
is ported (issue #3).

### The clock family's mechanism, and `rpc_uptime` ported

`Capability.CLOCK` names Core's `setmocktime`, absent from btclib-node.
`rpc_uptime` is ported: it is the one clock-family test needing the
clock alone; every other one also needs another mechanism (closes #6).

### `NodeAdapter` refuses an `extra_args` entry naming its own option

Reserved names are read out of `_command()` itself, so `-datadir`,
`-port`, `-rpcport` or `-regtest` -- any dash count, an `=value`, a `-no`
negation -- is refused rather than silently overriding it (closes #18).

### `BtclibNodeAdapter` authenticates a build that checks RPC credentials

A build gaining Core-style RPC authentication (btclib-node ISS #1070)
writes a cookie `BitcoindAdapter` already reads; the placeholder
credential this adapter carried is used only where a build has none (closes #25).

### A bitcoind-only test has a place of its own; `feature_torcontrol` is first

A `*_bitcoind_test.py` module with no `*_btclib_node_test.py` counterpart
needs no `Capability`; `TF2.md`'s per-test ledger spells such a row
`bitcoind only`. `feature_torcontrol` is the first (closes #23).

### `p2p_invalid_messages` gains more `Misbehaving` checks in the log family

Each is a wire disconnect and a `Capability.DEBUG_LOG`-gated log line;
btclib-node's own oversized-`inv` check fails (issue
btclib-org/btclib-node#1145). (issue #5)

### `feature_filelock` and `rpc_whitelist` join the disk family

`feature_filelock` passes on both nodes. `Capability.RPC_AUTH_CONFIG`
names `bitcoin.conf`'s RPC-auth keys, absent from the pinned
btclib-node build; `rpc_whitelist` is ported against it (issue #7).

### The option family's own census names its open candidates

`p2p_compactblocks_blocksonly` and `rpc_echo_payload` each need an
option alone; `TF2.md` names them, and why the rest of the re-measured
census is not a candidate (issue #3).

### The MiniWallet family's mechanism, and its first port

`MiniWallet` feeds its own coin cache from blocks it mines itself, never
`scantxoutset`. `feature_framework_miniwallet` is ported against
bitcoind, and skips on btclib-node for `Capability.MINE` (issue #4).

### `mempool_resurrect` and `mempool_spend_coinbase` join the MiniWallet family

`MiniWallet` gains `get_utxo`, a caller-named coin on
`create_self_transfer`/`send_self_transfer`, and `resync`; `build_fork`
builds a Core-style empty fork alongside it (issue #4).

### `p2p_invalid_messages` gains its size, drop and `addrv2` checks

`test_size` disconnects like `test_magic_bytes`; most other new checks
assert survival instead, and several rows fail on btclib-node, each
against its own already-filed issue, `TF2.md` naming which. (issue #5)

### README.md states the project's purpose, and how it is run

A non-regression suite for any node, beside or replacing Core's own
test framework; `CONTRIBUTING.md` gains the commands to run it
against your own checkout (issue btclib-org/btclib#2220).

### `rpc_users` completes the disk family

`-rpcauth`, `-rpccookieperms`, a malformed-`-rpcauth` roster, its own
interaction with named entries and `-norpcauth`, each against
`Capability.RPC_AUTH_CONFIG` or the new `RPC_AUTH_NEGATION` (closes #7).

### `core-master` and `btclib-node-main` are informational, not required

`core-master` builds `bitcoind` from Core's `master` and classifies its
own failures against `TF2.md`'s per-test ledger; `btclib-node-main`
installs from that project's `main` (issue #8).

### `NodeAdapter` waits for RPC by credential, not only by cookie

`NodeAdapter.__init__` gains an `rpc_auth` parameter, the credential a
caller already knows, so `start` waits on a node given `-rpcuser`/
`-rpcpassword` or `-norpccookiefile`, neither writing a cookie (closes #34).

### The softfork activation-height trio joins the option and MiniWallet families

`-testactivationheight` gains `Capability.TEST_ACTIVATION_HEIGHT`;
`feature_dersig`, `feature_cltv` and `feature_csv_activation` join the
option and MiniWallet families, `TF2.md` naming what each drops (issue #14).

### A fact that differs between builds is read from the build, for bitcoind too

`BitcoindAdapter` reads `Capability.MINE`'s own wallet dependency from the
running binary; `feature_torcontrol` and the newly ported
`p2p_bip434_feature` read the running build's own `getnetworkinfo` (closes #35).

### A Core developer runs the suite with the options `test_framework` gives them

`requires-python` moves to `3.12`. CONTRIBUTING.md maps `test_framework.py`
and `test_runner.py`'s options to pytest's, `--nocleanup`, `--tracerpc`,
`--timeout-factor` and `--v2transport` each gaining a real one (closes #36).

### The disk and MiniWallet families gain three single-mechanism leftovers

`feature_dirsymlinks` passes on both nodes; `feature_posix_fs_permissions`
fails on btclib-node (btclib-org/btclib-node#1198); `rpc_createmultisig` is
`bitcoind only`. (issue #4) (issue #6) (issue #7) (issue btclib-org/btclib#2220)

### Nodes connect to each other, disconnect, and wait for a mempool to agree

A mempool sync wait joins the block one, `rpc_setban` is ported in part,
a mixed bitcoind/btclib-node cluster gets a fixture, and `connect_nodes`
dials over v1 unless given `v2transport=True` (issue #43).

### The mempool-policy-option trio joins the option and MiniWallet families

`-datacarrier`, `-permitbaremultisig`, `-dustrelayfee` and `-bytespersigop`
each gain a `Capability`; `mempool_datacarrier`, `mempool_dust` and
`mempool_sigoplimit` join the option and MiniWallet families (issue #14).

### Bucket A's remaining files each need a mechanism, none of them the option's

`feature_prune_stale_fork`, `rpc_validateaddress`, `feature_nulldummy`,
`feature_versionbits_warning`, `rpc_signer` and
`feature_presegwit_node_upgrade` need a mechanism `TF2.md` names (issue #3).

### The `btclib-node` jobs gain the pinned `bitcoind`, and the mixed cluster runs

`btclib-node` and `btclib-node-main` install the same pinned release the
`bitcoind` job does and set `TF2_BITCOIND`, so the mixed cluster runs
there instead of skipping (closes #61).

### `feature_filelock`'s btclib-node test accepts either build's own wording

The released build's own uncaught RocksDB wording and the fixed build's
own clean "Cannot obtain a lock on directory" are both matched, rather
than only the first (closes #67).

### The mempool-cluster-option pair joins the option and MiniWallet families

`-limitclustercount` and `-limitclustersize` each gain a `Capability`;
`mempool_package_limits` and `mempool_updatefromblock` join them, and
`MiniWallet` gains multi-coin, chained and exactly-sized transfers (issue #14).

### `feature_filelock`'s bitcoind test pins which directory refused its lock

Each of its two tests matches Core's own whole refusal, the locked path
included, so a datadir refusal no longer passes the blocksdir test or the
reverse (closes #71).

### `NodeAdapter.stop` kills a node that ignores its termination

A node still running once the wait after `terminate` expires is killed
rather than left holding its datadir and ports, and a `TimeoutError`
carrying its stderr says so (closes #76).

### `test_addrv2_unrecognized_network` is ported, over `-debug=addrman`

`-debug=addrman` joins `-debug=net`, so the address-manager lines Core's own
`test_addrv2_unrecognized_network` asserts are in the log it reads, and
that test joins `p2p_invalid_messages`' `addrv2` checks (issue #5).

### A node whose start fails is killed, and every teardown stop is kept

`NodeAdapter.start` kills its process before raising, and the fixtures that
stop several nodes stop each one and chain every error rather than keeping
only one (closes #79).

### Transaction upload, UTXO hash, descriptor activity and block stats ported

`feature_utxo_set_hash`, `rpc_getdescriptoractivity` and `rpc_getblockstats`
join the MiniWallet family, each RPC with its own capability; `p2p_leak_tx`
joins it and the clock family, and `Peer` gains `sync_with_ping` (issue #14).

### `NodeAdapter.restart` takes replacement `extra_args` for one start

`restart([...])` uses them for that start alone, as Core's `restart_node`
does, and `rpc_setban`'s `-whitelist` and `-bantime` sections are ported on
it (closes #51).

### `feature_fastprune`, `p2p_eviction` and `rpc_scanblocks` are ported

Each gains a `Capability` for what it asks of a node, `btclib-node`'s adapter
declaring inbound eviction wherever its build has it; `tool_utxo_to_sqlite`
stays out, its subject a Core script rather than a node (issue #14).

### `MiniWallet` knows which of its coins a block holds

`get_utxo` and a new `get_utxos` take Core's `confirmed_only` and
`mark_as_spent`, an unnamed coin being the largest matured one as in Core, and
`resync` asks `gettxout` which coins a block mined elsewhere holds (closes #69).

### `feature_presegwit_node_upgrade` joins the option family

A lower `-testactivationheight=segwit@N` refuses to restart a chain mined
past it, in Core's own words, and `-reindex` upgrades it (issue #3).

### `NodeAdapter.stop` reports a crashed node, and `start` refuses a second

`stop` raises on a node that exited with a code other than 0, carrying its
stderr; a second `start` raises; `mine` loads its wallet after a restart or
over a reused datadir (closes #84) (closes #86) (closes #92).

### `tf2_master_verdict` can answer "candidate regression"

`classify` compared `TF2.md`'s abbreviated pin with the API's full sha, so
every master-only failure read as a stale port; the pin is now matched as a
prefix (closes #83).

### `MiniWallet`'s self-transfers take Core's fee, version and sequence

`create_self_transfer` and `send_self_transfer` take Core's `fee_rate`, `fee`,
`version`, `locktime` and `sequence` with its defaults, the multi pair the last
three; fees are in satoshis, and broadcasts pass `maxfeerate` 0 (closes #103).

### `mempool_dust`'s refusal cases assert the reason is dust

The below-threshold test asserts `testmempoolaccept`'s reject reason, not only
its `allowed` flag, as Core's own `mempool_dust.py` does at v31.1 (closes #93).

### `rpc_setban`'s restart check reads `listbanned`, then bitcoind's own log

`listbanned` is asserted right after `restart()`, and the refused dial is
read over `assert_debug_log` against bitcoind's own `dropped (banned)`, not
`connect_nodes`'s bare `TimeoutError` alone (closes #94).

### `capability.py` names its own hookwrapper, not an autouse fixture

`capability.py`'s module docstring names the mechanism that turns
`MissingCapabilityError` into a skip as `tests/conftest.py`'s own
`pytest_runtest_call` hookwrapper (closes #97).

### `nocleanup_bitcoind_test` stops its node on a failing assertion too

The datadir-survives-`stop` assertion now runs inside a `try`/`finally`, so
a failure no longer leaves the node running past the test (closes #95).

### `free_ports` reserves every port a fixture needs before any bind

`free_port`, called once per port, can hand two of them the same one; the
fixtures in `tests/integration/conftest.py` now draw theirs from `free_ports`,
which holds every probe open until all are bound (closes #85).

### `mempool_util.fill_mempool` pushes a node's mempool to eviction

Ported from Core's own `test_framework/mempool_util.py`, over a throwaway
`MiniWallet`: disposable, rising-fee self-transfers until `mempoolminfee`
rises above `minrelaytxfee` and the lowest fee-rate one is evicted (closes #70).

### Every integration module building its own adapter draws its ports from `free_ports`

Each drew its `rpc_port`/`p2p_port` pair from two separate `free_port()` calls,
the same collision `free_ports` exists to close; a module building several
adapters before starting any now draws all their ports at once (closes #115).

### The docs describe the tree's adapter as it stands, not as its first step

`CLAUDE.md`, `CONTRIBUTING.md`, `tests/README.md` and the package
docstring point at `CONTRIBUTING.md`'s public-surface list rather than
each naming a stale subset of it (closes #96).

### The killed-node test stops its own node on a failure before `stop`

The window between `start()` and this test's own first `stop()`, in both
twins, now runs inside a `try`/`finally` that kills the process only if it
is still alive (closes #114).

### A reference to another repository's issue is qualified with its owner and name

Bare `ISS 2220` in a comment or docstring resolved to this tracker,
where no such issue exists; citations of btclib and btclib-node now
carry the owner and repository, `TF2.md`'s own form (closes #100).

### `_wait_for_rpc` tells a node's own answer from silence

An `RpcError` other than `-28 RPC_IN_WARMUP`, or an `HttpError` carrying 401
or 403, fails at once with the node's own error as its cause, instead of
waiting out the startup timeout and reporting `TimeoutError` (closes #98).

### A shared, scaled `node.wait_until` replaces the unscaled test-local waits

Two modules' own polling loops ignored `--timeout-factor`; both now share
`node.wait_until`, and a `peer.receive`/`future.result` timeout in two
other modules is scaled the same way (closes #90).

### `tests/integration/conftest.py`'s hooks are thin calls into `tests/conftest.py`

`_stop_all` and the bodies of `pytest_sessionfinish` and
`pytest_testnodedown` now live in `tests/conftest.py`, outside
`[tool.coverage.run]`'s `omit`, and are unit-tested there (closes #101).

### A require-only btclib-node stub fails once its capability is declared

Every `*_btclib_node_test.py` test whose body was only `del`/`require(...)`
now ends in `pytest.fail`, and asks for the capabilities its bitcoind twin
does; `tests/require_only_stub_test.py` holds both to it (issue #82).

### Each `NodeAdapter` start redirects the node's stderr into a file of its own

Each start writes under the datadir's `stderr/`, as Core's `TestNode.start`
does, and `stop` reads its own start's file: a second adapter over one datadir
overwrote the one `node-stderr.log` a running node's `stop` read (closes #105).

### `rpc_getdescriptoractivity`'s payments each run on a node of their own

`test_activity_in_block` and `test_no_mempool_inclusion` pay 1 BTC from a
fresh node, as Core's own file does, not from the shared one, where a long
enough chain leaves every coinbase the test matures worth less (closes #127).

### `UA_COMMENT` and `V2TRANSPORT` measure both `btclib-node` builds

`cli.py`'s `_build_parser` is gone from `btclib-node`'s `main`, replaced by a
module-level `_OPTIONS` dict; the `UA_COMMENT` and `V2TRANSPORT` docstrings
now measure both the released build and `main` (closes #59).

### Every test runs under a per-test timeout

`pytest-timeout` joins `harness`, and `[tool.pytest.ini_options]`'s `timeout`
fails a test that hangs by name, scaled by `--timeout-factor` with the waits
beneath it (closes #91).

### A `NodeAdapter` start that times out says what the node was doing

Its `TimeoutError` names the failures waited out, as Core's
`wait_for_rpc_connection` does, then the start's stderr and what it appended to
bitcoind's `debug.log` or btclib-node's `history.log` (closes #134).

### `BtclibNodeAdapter` declares `RPC_AUTH_NEGATION` on a build reading `-norpcauth`

A probe asks the build's own `cli.build_config` whether `-norpcauth` discards
an `-rpcauth` given before it, so `rpc_users`'s negation test runs against
`btclib-node`'s `main` and skips against the release (closes #130).

### `BitcoindAdapter` passes `-rpcallowip`, so its `-rpcbind` takes effect

A taken `127.0.0.1` RPC port now fails bitcoind's init and `start` on the exit
code, where bitcoind ignored `-rpcbind` alone, served RPC on `::1` and left
`start` to time out (closes #135).

### `--tracerpc` traces every adapter a test builds

Test modules and `mixed_cluster` built their adapters without it; each now goes
through the `make_adapter` fixture, and `tests/tracerpc_reach_test.py` fails on
one that bypasses it without naming its own `trace_rpc` (closes #89).

### `rpc_getblockstats`'s `utxo_size_inc` expectations follow the running build

A coin is charged its serialized `TxOut` plus `PER_UTXO_OVERHEAD`, one byte
less from Core `v32.0.0` on (bitcoin/bitcoin#31449), read off
`getnetworkinfo`'s `version`, so Core's `master` passes too (closes #107).

### `feature_blocksdir` matches the whole refusal on both btclib-node builds

The refusal is matched as the node's whole stderr, the path included, in Core's
wording `main` writes or the released build's own, so `main` no longer fails it
and bitcoind's twin pins its text the same way (closes #141).

### `BtclibNodeAdapter` mines, on a build connecting a block with no peer

`mine` builds each block client-side and submits it; a probe of the build's own
`main.update_chain` declares `MINE` against `btclib-node`'s `main` and not the
release, where a solo node never connects a submitted block (closes #56).

### `tf2_master_verdict` names an unchanged Core file as measured

A master-only failure whose Core file has not moved since its pin reads "file
unchanged since the pin" where it read "candidate regression", naming no owner:
the port may never have matched that file, so it is checked first (closes #143).

### `BtclibNodeAdapter` declares `BAN` on a build serving a ban list

A probe of the build's own `rpc.callbacks.callbacks` declares `BAN` where it
names `setban`, `listbanned` and `clearbanned`, as `btclib-node`'s `main` does
and the release does not (closes #140).

### `tf2_master_verdict` reads the data files a Core test loads

A master-only failure reads "file unchanged since the pin" only where no data
file its Core test loads has moved either, where the entry closing #143 names
the test file alone; a moved data file is a stale port, named (closes #146).

### `check_vendored_vectors` does not read a removed pin as changed content

A pin whose file upstream deleted or renamed is reported as the commit that
removed it, which the report says may be a deletion or a rename; "no commit"
names a path the branch walked never held (closes #150).

### A `NodeAdapter` starts on the chain its caller names

`chain=` picks `main`, `test`, `testnet4`, `signet` or `regtest`, the default;
`BtclibNodeAdapter` refuses `testnet4`, and any chain but regtest starts with
`-connect=0`, drawing no peer and asking no seed (closes #63).

### `BitcoindAdapter`'s wallet probe is checked against a build tree's record

Only `MINE` rests on a `test/config.ini` component, `ENABLE_WALLET`; the adapter
still probes the binary, and a test holds `MINE` to that file in a build tree
and on for a release, which guix builds with the wallet (closes #53).

### The `btclib-node` jobs fail when their tests never reached a node

Each fails on an empty report or on a skip that is not a capability's: an
`import btclib_node` raising after a good install skips every test, and pytest
alone exits 0 on that (closes #87).

### `btclib-node` keeps its own interpreter rather than a dependency group

`pyproject.toml`'s `[dependency-groups]` comment says why: btclib-node's floor
sits above the interpreter `.python-version` names, and `TF2_BTCLIB_NODE_PYTHON`
names any build of it -- a release, its `main`, a checkout (closes #42).

### `rpc_users.py`'s btclib-node test accepts Core's malformed `-rpcauth` wording

A malformed `-rpcauth` matches either whole stderr: Core's "Unable to start HTTP
server", which btclib-node's `main` writes, or the older "Invalid -rpcauth
argument." (closes #159).

### `REVIEWING.md` lets a filed issue carry its fix

An issue filed from a review may say the fix where one is known: *What is
filed, and what is not* dropped its "no fix", the filing bar standing as it
was (issue btclib-org/.github#1378).

### The `btclib-node` jobs report what moved against `TF2.md`

Each compares its report with the ledger's `btclib-node` column, reading the
verdict a cell gives its own build: a known failure no longer colours the job,
and a row that moved, one now passing included, does (closes #88).

### `_negates_rpcauth` reads `rpc_auth_invalid`, not a bare return

Since btclib-node keeps a malformed `-rpcauth` there rather than raising
(issue btclib-org/btclib-node#1210), a bare return no longer says
`-norpcauth` discarded it (closes #160).

### `TF2.md`'s btclib-node fail cells carry a build qualifier

A fail cell claimed every build though btclib-node's `main` already passes
it; it now carries the skip cells' own build-qualified form, and the prose
explaining it, ledger and tests alike, names the released build (closes #157).

### `feature_nulldummy` is ported, its multisig spends built by the test

Every step of Core's own file runs, each spending a multisig that requires no
signature, NULLDUMMY reading the dummy whatever the required count; the test
builds each scriptSig and witness, and `MiniWallet` gains nothing (closes #64).

### `p2p_disconnect_ban`'s `disconnectnode` half is ported

It passes on bitcoind and skips on btclib-node, which has no `disconnectnode`
RPC. `TF2.md` hands every other node-linking file to ISS 14, this file's
`setban` half among them, unless the census disqualifies it (closes #43).

### One body runs a Core test against both nodes

`p2p_block_sync`, `p2p_compactblocks_hb` and `p2p_invalid_locator` call one
body from both nodes' tests, so a btclib-node build declaring the capabilities
runs Core's scenario rather than a stub's `pytest.fail` (issue #125).

### `feature_nulldummy`'s multisig spends are signed, as Core's own are

Each spends a 1-of-1 multisig the test signs with btclib, so a node reads the
dummy beneath a signature; a tampered dummy leaves the signature valid, and
NULLDUMMY is still the only refusal (closes #165).

### `rpc_validateaddress` is ported, with Core's address tables

On bitcoind started on the main chain, each of Core's invalid addresses answers
its own error and `error_locations`, and each valid one its own `scriptPubKey`;
btclib-node's test skips on `Capability.VALIDATE_ADDRESS` (closes #153).

### `feature_dersig`'s non-DER signature is ported, signed with btclib

`mini_wallet.py` gains Core's own `RAW_P2PK` output and its signature, and
`feature_dersig`'s spend of it is mined before BIP66 and refused after, by the
mempool and a block alike (issue #167).

### Two MiniWallet mempool tests and `feature_utxo_set_hash` run one body

`mempool_resurrect`, `mempool_spend_coinbase` and `feature_utxo_set_hash` call
one body from both nodes' tests, each reading a block's transactions off the
raw `getblock` both nodes serve (issue #125).

### `rpc_setban` runs one body per test on both nodes

Each of its tests calls one body from both nodes' tests, so a btclib-node build
serving the ban list runs Core's scenario rather than a stub's `pytest.fail`
(issue #125).

### A node can be made to dial the test, and `p2p_addrfetch` is ported

`peer.Listener` accepts a node's own outbound connection as a `Peer`, and
`NodeAdapter.add_outbound_connection` asks for one of a chosen type under
`Capability.TYPED_OUTBOUND`, which btclib-node declares on no build (issue #44).

### `rpc_getdescriptoractivity`'s remaining subtests are ported

Several addresses at once, a confirmed payment beside an unconfirmed one, a
receive and its spend over two blocks, and a `RAW_P2PK` script with no address,
the last spent under `mini_wallet.py`'s signing helper (issue #167).

### `rpc_echo_payload` is ported, with `Capability.RPC_WORK_QUEUE`

Under Core's `-rpcworkqueue=2` and `-rpcthreads=2`, bitcoind answers every
concurrent `echo` and `sendrawtransaction`, or refuses it with HTTP 503, never
timing out; btclib-node skips on `Capability.RPC_WORK_QUEUE` (issue #3).

### `p2p_eviction` runs one body on both nodes

Both nodes' tests call one body, which asks the node's `-help` whether it splits
its inbound slots by relay, so a btclib-node build that evicts and mines runs
Core's scenario rather than a stub's `pytest.fail` (issue #125).

### The log family's census is recorded, and more of its checks ported

`p2p_handshake`'s redundant `verack`, `p2p_addr_relay`'s oversized `addr` and
`p2p_addrv2_relay`'s late `sendaddrv2` run on both nodes; `TF2.md` names where
every other Core test reading the log goes (issue #5).

### The `-blocksonly`, `getblockfilter` and `getblockfrompeer` tests are ported

`p2p_compactblocks_blocksonly`, `rpc_getblockfilter` and `rpc_getblockfrompeer`
skip on btclib-node; `Peer` gains Core's `last_message` and a `handshake`
offering chosen services (issue #3).

### `feature_cltv`'s failure reasons are ported, with `Capability.ACCEPT_NON_STANDARD`

BIP65's failure reasons are mined before activation, then refused by
`testmempoolaccept` under Core's `-acceptnonstdtxn` and by `submitblock`; one
body runs on both nodes (issue #167).

### `feature_framework_miniwallet` runs one body per test on both nodes

Each test calls one body over either node, so a btclib-node build that mines
runs it rather than a stub's `pytest.fail`; `confirmed_only`, `fee_rate` and
TRUC have `TF2.md` rows of their own (issue #125).

### `mini_wallet.build_next_block` builds one block on the node's tip

It returns a solved, unsubmitted block paying a chosen coinbase `scriptPubKey`,
carrying chosen transactions at a chosen header version; the integration tests
that kept their own copy of the builder call it instead (closes #178).

### `p2p_node_network_limited` is ported, and the option family's census recorded

`p2p_node_network_limited` runs on bitcoind and skips on btclib-node, and
`setnetworkactive` is `Capability.SUSPEND_NETWORK`. `TF2.md` records the option
family's census and where each file it lists goes (closes #3, closes #185).

### `rpc_getdescriptorinfo` is ported, with Core's descriptor table

bitcoind answers Core's descriptors with their checksums, flags and multipath
expansions, and refuses each malformed request with Core's own error;
btclib-node skips on `Capability.DESCRIPTOR_INFO` (closes #174).

### `p2p_timeouts`, `p2p_ping` and `mempool_expiry` are ported

Each runs one body on both nodes under Core's own `-peertimeout` or
`-mempoolexpiry`, the node's clock moved by `setmocktime`; btclib-node skips on
the new `Capability.PEER_TIMEOUT` and `Capability.MEMPOOL_EXPIRY` (issue #14).

### `node-integration.yml` installs bitcoind with `btclib-org/.github`'s script

The `btclib-node` jobs use it, and the `install-bitcoind` action goes (issue
btclib-org/.github#1373); the `bitcoind` job exempts btclib-node's absence by
its skip reason, not its module name (issue btclib-org/.github#1377).

### `test: every job passed` accepts its own `needs` job listed unfinished

A `needs` job the jobs listing still shows unfinished is accepted where its own
result is `success` or `skipped`; any other unfinished job is still refused
(issue btclib-org/.github#1395).

### `REPOSITORY.md` reads back classic signatures off and SHA pinning on

Classic `required_signatures` reads `false`, and `allowed_actions` and
`sha_pinning_required` are read back, section 11 having the reasons (issue
btclib-org/.github#1409).

### `rpc_createmultisig`'s spend half is ported

bitcoind signs each multisig spend in two parts, merges them and mines it, and
`createmultisig`'s key-count limits and legacy fallback are checked;
btclib-node skips on `Capability.SIGN_RAW_TRANSACTION` (issue #167).

### `feature_dersig`, `rpc_uptime` and option tests run one body on both nodes

`feature_uacomment`, `rpc_uptime`, `v2transport_option`, `rpc_echo_payload`,
`feature_fastprune`, `mempool_fill` and `feature_dersig` call one body per test,
which asks the running node rather than its class for capabilities (issue #125).

### `feature_csv_activation`'s body is ported, with `Capability.INVALIDATE_BLOCK`

BIP68, BIP112 and BIP113 are checked block by block around Core's own
activation height; one body runs on both nodes, and
`mini_wallet.build_next_block` takes the time its block carries (closes #167).

### `feature_nulldummy` and mempool option tests run one body on both nodes

`feature_nulldummy`, `feature_presegwit_node_upgrade`, `mempool_datacarrier`,
`mempool_dust`, `mempool_package_limits`, `mempool_sigoplimit` and
`mempool_updatefromblock` call one body per test, over either node (issue #125).

### `p2p_add_connections` and the rest of `p2p_handshake` are ported

bitcoind dials typed outbound peers and drops a feeler, a peer short of the
services its type expects and a dial to itself; `manual` is asserted per build.
btclib-node skips on `Capability.TYPED_OUTBOUND` (issue #44).

### `feature_includeconf` and `feature_reindex_init` are ported

btclib-node runs `feature_includeconf`'s refusals and warning, skipping the
include order on `Capability.UA_COMMENT`, and skips `feature_reindex_init` on
the new `Capability.REINDEX_AFTER_FAILURE` (issue #14).

### `rpc_generate`, `rpc_signrawtransactionwithkey` and `rpc_scantxoutset` are ported

bitcoind mines blocks to a given address or descriptor, signs with given keys
and searches its UTXO set by descriptor; `Capability.GENERATE` and
`Capability.SCAN_UTXO_SET` are new, and btclib-node skips each (issue #4).

### `test: every job passed` reads a lagging row again and judges `needs` results

A `needs` row still listed unfinished is read again, up to three times ten
seconds apart, before being accepted (issue btclib-org/.github#1416); a `needs`
result neither `success` nor `skipped` fails (issue btclib-org/.github#1424).

### More p2p tests run one body on both nodes

`p2p_disconnect_ban`, `p2p_invalid_messages` but its `addrv2` checks,
`p2p_leak`, `p2p_leak_tx` and `p2p_net_deadlock` call one body per test, over
either node (issue #125).

### `feature_proxy` is ported in part, on a mock SOCKS5 proxy

`socks5.Socks5Proxy` records what a node asks a SOCKS5 proxy for, and bitcoind
routes each network through the proxy `-proxy` or `-onion` gives it.
btclib-node skips on `Capability.PROXY` (issue #47).

### The first node-wallet tests are ported, with `Capability.NODE_WALLET`

`wallet_signmessagewithaddress`, `wallet_blank` and `wallet_coinbase_category`
run against bitcoind's own wallet, reached at `/wallet/<name>`; btclib-node
skips on `Capability.NODE_WALLET` (issue #45).

### `p2p_initial_headers_sync` and `p2p_sendtxrcncl` are ported

The headers timeout drops a stalling sync peer and spares a `noban` one; BIP330's
`sendtxrcncl` is checked sent, withheld, ignored and refused, gated on
`Capability.TX_RECONCILIATION` and `Capability.PEER_BLOOM_FILTERS` (issue #44).

### RPC stubs and `feature_blocksdir` run one body; its refusal is Core's alone

`feature_blocksdir`, `rpc_validateaddress`, `rpc_scanblocks`,
`rpc_getblockstats`, `rpc_getdescriptorinfo` and `rpc_getdescriptoractivity` run
one body per test; the released btclib-node fails the refusal (issue #125).

### The bodies calling `generateblock` ask for `Capability.GENERATE`

`feature_framework_miniwallet`'s `confirmed_only` and a
`mempool_updatefromblock` test skip where a node lacks it: btclib-node's
`main` skips `confirmed_only` rather than failing it (closes #207).

### `feature_reindex` and `feature_reindex_readonly` are ported

bitcoind reindexes back to its height, over blocks out of order, after a
stopped reindex and from a read-only block file, and logs Core's `reindex`
category; btclib-node skips on the new `Capability.REINDEX` (issue #14).

### `TF2.md`'s `rpc_setban` and `p2p_eviction` cells name btclib-node's fixes

`rpc_setban.py`'s non-IP row passes past btclib-org/btclib-node#1218;
`p2p_eviction.py`'s fails on some runs past btclib-org/btclib-node#1179, a
`ping` overtaking the `tx` before it (btclib-org/btclib-node#1410) (issue #212).

### `feature_filelock` and `rpc_users` match a refusal in Core's wording alone

btclib-node's lock refusal and malformed `-rpcauth` refusal are each matched in
Core's wording, as `feature_blocksdir`'s is: the released btclib-node fails
`feature_filelock` (closes #211).

### `p2p_feefilter` is ported

BIP133's `feefilter` is checked sent to an inbound peer and withheld from a
`forcerelay`, a block-relay-only and a `-blocksonly` one, and a peer's own
filter is checked to withhold announcements below it until lifted (issue #44).

### `Peer.sync_with_ping` is a barrier on a node processing messages in order

Its docstring promises the barrier only on a node processing each peer's
messages in order, as Core's does, and not on one answering a `ping` ahead
of them (btclib-org/btclib-node#1410) (issue #212).

### `p2p_message_capture` and `feature_blocksxor` are ported

bitcoind captures a peer's messages under `-capturemessages` and refuses
`-blocksxor=0` over a stored key; btclib-node skips on the new
`Capability.CAPTURE_MESSAGES` and `Capability.BLOCKS_XOR` (issue #14).

### More node-wallet tests are ported, and `wallet_disable` on bitcoind alone

`wallet_createwalletdescriptor`, `wallet_sendmany` and `wallet_timelock` run
against bitcoind's own wallet, btclib-node skipping each on `NODE_WALLET`;
`wallet_disable` runs against bitcoind alone (issue #45).

### `feature_proxy`'s remaining nodes and refused starts are ported

`socks5.Socks5Proxy` also listens on IPv6 loopback or a unix socket. bitcoind is
checked through either, and under `-cjdnsreachable`, `-i2psam` or a per-network
`-proxy`, and on every start Core refuses; btclib-node skips (issue #47).

### `mempool_accept_wtxid` and `rpc_orphans` are ported

bitcoind tells two children sharing a txid apart by wtxid, and keeps a child
sent ahead of its parent as an orphan. btclib-node skips `rpc_orphans` on the
new `Capability.ORPHANAGE`; its `main` fails `mempool_accept_wtxid` (issue #4).
