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
