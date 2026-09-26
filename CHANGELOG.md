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
