# The tf2 ledger

One entry per Python file of Bitcoin Core's
`test/functional/test_framework/`, naming what covers it in `btclib`,
what the covering module asserts, and the revision of that file the
entry was read at.

What it is for is
[ISS 198](https://github.com/btclib-org/btclib/issues/198)'s "strictly
equivalent", the phrase on which offering anything back to Core rests.
That is a claim about a moving target: Core's framework changes, so an
equivalence measured against a revision nobody wrote down is an
equivalence nobody can re-check. An entry here turns "btclib covers
`blocktools`" into a sentence with a truth value -- which `blocktools`,
asserted by what, and what has moved upstream since.

It makes the gap visible in the other direction too. Re-deriving what is
left of Core's framework means reading the directory again, which is
work that starts going stale the moment it is finished; this is that
reading written down once, and moved by whatever moves it.

The file moved here from `btclib`'s own tree
([ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220)),
which held it while tf2 had no repository of its own. A verdict names
btclib's covering module wherever btclib covers the file, and this
repository's own module or test wherever this repository does;
`CONTRIBUTING.md`'s *The public surface* names the modules it holds.

## Reading an entry

An entry is a `###` heading naming the file's path in Core, a fenced
block pinning it, and a verdict with what stands behind it.

`repo`, `path` and `commit` are the pin, and `behind` is how many
upstream revisions of that path have landed since. That is the grammar
`.github/scripts/check_vendored_vectors.py` parses, which
`.github/workflows/vendored-vectors.yml` runs over this file weekly: a
pin here that has moved says a verdict is now a claim about a file that
has moved.

An entry's `commit` is the tip of the path the entry names, so `behind`
reads zero and a re-check can clear it. A repository-wide revision is a
perfectly good "this is the tree I read" pin, and `contents/<path>?ref=<sha>`
resolves one; what it settles is the tree and not the path. It is the
tip of a path only where nothing on the default branch has touched that
path since, which is a fact about that history rather than about the
pin, so a per-path `behind` cannot be counted on to read zero for such a
revision, and a ledger whose whole purpose is re-checkability takes the
per-path pin, which is the one that goes stale loudly.

## The verdicts

- **covered** -- btclib publishes the same thing, and a test asserts it.
- **covered in part** -- some of the file's surface is btclib's and some
  is not; the entry names both halves.
- **vendored** -- btclib holds Core's own file, with the attribution.
- **tf2's by decision** -- an issue decided it out of btclib, and the
  entry names that issue.
- **tf2's (harness)** -- it drives a node: a process, an RPC client, a
  socket, an event loop. Nothing in btclib answers it, and nothing is
  meant to; this repository's own adapters and harness are where it
  lands, and an entry this repository already covers names what does.
- **empty upstream** -- the file has no content at the pinned commit.
  The entry is there so that content arriving in it moves the pin.

## Re-checking a pin

The path stands in a fence of its own, sitting inside the API argument
rather than at the end of the command; the fence below reads it as
`${entry_path:?}`, the shell's must-be-set form, so a paste of that
fence alone fails naming the variable rather than asking about whatever
the shell already held.

The variable is `entry_path` and not `path`, which is the name the
argument wants: in `zsh` -- the shell this is read in -- `path` is tied
to `PATH` as an array, so assigning a file path to it replaces the
reader's `PATH` with that one entry and the next command in their
terminal is not found.

```shell
entry_path=<the path the entry gives>
```

```shell
gh api --method GET repos/bitcoin/bitcoin/commits \
    -f "path=${entry_path:?}" -f per_page=1 \
    --jq '.[0].sha + "  " + .[0].commit.committer.date[:10]'
```

The answer is the entry's own `commit` where nothing has moved. Any
other commit means the file changed after it was read, and the entry's
verdict is then a claim about a file that is no longer there.

**What a per-pin re-check cannot catch is a file Core gains.**
`tests/tf2_ledger_test.py` runs offline and holds this file to a
transcription of Core's directory rather than to Core, so a new
`test_framework/*.py` upstream is invisible to it and to the pin
re-check above, which reads only the entries a ledger already carries
([ISS btclib-org/btclib#1751](https://github.com/btclib-org/btclib/issues/1751)).
`.github/scripts/tf2_ledger_census.py` is the read that answers it: a
recursive listing of the directory at a fresh commit, compared against
this file's own entries in both directions, with `.truncated` checked
rather than assumed and the `contents` endpoint never used -- it lists a
directory non-recursively, so it would answer without `crypto/*.py` and
report every file one directory down as gone. `vendored-vectors.yml`
runs it weekly, under a title distinct from the per-pin drift issue, so
a gained file and a stale pin are never the same issue.

No entry carries a `blob`, which is where this file parts from
`tests/_data/README.md`: nothing in this tree is a copy of any file
below but the RIPEMD-160 implementation, whose own entry names where
that comparison lives instead of making one here.

## Citing the framework from btclib and from tf2

A module citing one of these files names the file and the *function*,
carrying no revision of its own and no line number: an edit upstream
moves a line with nothing going red, so what a citation names beside the
file is the function. `script/sig_hash.py`'s `segwit_v0` cites
`SegwitV0SignatureHash` of `test/functional/test_framework/script.py`.
That rule is tf2's alone now, `TF2.md` and every citation of it having
left btclib's tree the day this issue's step 0 landed.

**A citation of Core's C++ is a different thing**, and none of the above
reaches it. This file pins no C++ path, so such a citation has no entry
here to leave a revision to.

**A vendoring line is not a citation.** `_ripemd160.py` is Core's own
file, and the revision its docstring carries says which bytes were
copied, beside the attribution the licence asks for. That pin belongs
where the copy is, and moves when the copy does -- it stays in `btclib`,
not here, since the copy is there.

## bitcoin/bitcoin

### `test/functional/test_framework/__init__.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/__init__.py
commit  c28ee91db07ce82e134d500ddeb5600363c98048  2017-03-20
behind  0 revisions; that commit is the tip of the path
```

Verdict: **empty upstream**. The package marker, with no content at the
pinned commit. The entry is here so that content arriving in it moves
the pin rather than passing unnoticed.

### `test/functional/test_framework/address.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/address.py
commit  4dbaa7cc65b9546d07f1f9bfc8fb912b6fb20a5e  2026-06-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `b58.address_from_h160` and `b58.h160_from_address`
for the base58 addresses, `b32.address_from_witness` and
`b32.witness_from_address` for the segwit ones, each over the codec
below it -- `base58` and `bech32`, a split Core's file does not make.
`script.script_pub_key`'s `address`, `addresses` and `type_and_payload`
are the `address_to_scriptpubkey` direction.
`create_deterministic_address_bcrt1_p2tr_op_true` composes
`script.taproot.output_pubkey` over `tree_helper` with `b32.p2tr`, so it
is a convenience of tf2's assembled from parts btclib already has.

### `test/functional/test_framework/authproxy.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/authproxy.py
commit  f42226d526ebb3eb9217e738108e4f8148a1b069  2026-06-04
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. Reaching a node over JSON-RPC is the
`bitcoin-core-rpc` package, which this repository depends on directly
and which `btclib.fetch.bitcoin_core` also builds on. Core's file is not
a vendoring candidate either: its header puts it under the GNU Lesser
General Public License, which is not this project's.

### `test/functional/test_framework/blockfilter.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/blockfilter.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `block/block_filter.py` holds both halves.
`BasicBlockFilter` maps an element into the filter's range as
`bip158_basic_element_hash` does, keyed on the block hash, and its
`from_block` selects what `bip158_relevant_scriptpubkeys` selects --
the previous output script of every non-coinbase input, and every output
script BIP158 does not exclude -- with the utxo set handed in through
`prevout_scripts_from_utxos` rather than read off a node. Each draws the
output rule from a different place, and btclib's is the one the BIP
states: Core's Python asks whether the output type is `nulldata`, where
btclib tests the first byte for `OP_RETURN` as Core's own C++ does.
`p2p/block_filters.py` carries BIP157's messages over it.

### `test/functional/test_framework/blocktools.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/blocktools.py
commit  1966621b76885257b4b4e44aab4712e9f84313e6  2026-05-13
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `block/build.py` is `create_coinbase`,
`create_block` and `add_witness_commitment`:
[ISS 1118](https://github.com/btclib-org/btclib/issues/1118) put
`build_coinbase`, which pays `consensus.subsidy` at a height and commits
to that height as BIP34 requires, beside `build_block`, which assembles
the block over a list of transactions and its witness commitment.
`block/proof_of_work`'s `target_from_bits` and `bits_from_target` are
what `nbits_str` and `target_str` print, and `script.sig_ops`'s
`sig_op_count` is what `get_legacy_sigopcount_tx` counts.
`create_tx_with_script`, `create_witness_tx` and `send_to_witness` spend
against a node's wallet, and are tf2's.

### `test/functional/test_framework/compressor.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/compressor.py
commit  b34fdb5ade0b48384636f8c7c9673554bf82cedf  2025-03-04
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**.
[ISS 1123](https://github.com/btclib-org/btclib/issues/1123): the
chainstate encoding is the format Core reserves for itself, where
`fetch/` depends on the interface Core publishes for everyone else.
`util.util_xor`, the obfuscation of Core's own block files, went to tf2
with it.

### `test/functional/test_framework/coverage.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/coverage.py
commit  fa71c15f8610816a6ee0426cd396315da3d27c30  2025-11-26
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. It records which RPCs a run reached.
Nothing in btclib answers it.

### `test/functional/test_framework/crypto/bip324_cipher.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/bip324_cipher.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**.
[ISS 1066](https://github.com/btclib-org/btclib/issues/1066) drew the
line: what btclib builds out of the standard library is in, and a
hand-rolled cipher is not. BIP324's v2 transport is tf2's to hold, with
its own cipher, as Core holds its own (rule 6 of
[ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220)).

### `test/functional/test_framework/crypto/chacha20.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/chacha20.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**. ISS btclib-org/btclib#1066, the same line.
`muhash.py` carries a private `_chacha20_block` because `MuHash3072`'s
element hash is a keyed ChaCha20 keystream and nothing else in btclib
needs one; its `__all__` publishes `MuHash3072` alone.

### `test/functional/test_framework/crypto/ellswift.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/ellswift.py
commit  3fd68a95e68b4c6f3bb6c59d41dd196001110f3a  2026-04-07
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `ecc/ellswift.py`: `create_var` for
`ellswift_create`, `encode_var` for `xelligatorswift`, `decode_var` for
`xswiftec`, and `xdh` for `ellswift_ecdh_xonly`, over `_xswiftec_var`
and `_xswiftec_inv_var`.

### `test/functional/test_framework/crypto/hkdf.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/hkdf.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `kdf.hkdf` is Core's `hkdf_sha256`, and
`kdf.hkdf_extract` and `kdf.hkdf_expand` stand beside it where Core's
file offers the one-shot alone
([ISS 1080](https://github.com/btclib-org/btclib/issues/1080)).

### `test/functional/test_framework/crypto/muhash.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/muhash.py
commit  fec2ca6c9a8a8e44b6e4d51c4ef7fa6eaca6e446  2023-09-29
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `muhash.MuHash3072` is Core's class operation for
operation -- `insert`, `remove` and the digest are all the pinned file
has -- and `coinstats.py` is what feeds a utxo set through one. btclib's
`serialize` and `deserialize` answer Core's C++ class instead, which the
module says where it implements them.

### `test/functional/test_framework/crypto/poly1305.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/poly1305.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**. ISS btclib-org/btclib#1066, the same
line: an authenticator written out by hand is what that issue put on
tf2's side.

### `test/functional/test_framework/crypto/ripemd160.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/ripemd160.py
commit  08a4a56cbcfa54366c2c0bb52bb147fc2740edc5  2023-09-10
behind  0 revisions; that commit is the tip of the path
```

Verdict: **vendored**. `btclib`'s `src/btclib/_ripemd160.py` is Core's
file, MIT and therefore that project's licence too, for an interpreter
whose `hashlib` offers no RIPEMD-160; its docstring carries the
attribution, the revision it was taken at, and every delta from
upstream. That vendoring lives in `btclib`, not here.

### `test/functional/test_framework/crypto/secp256k1.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/secp256k1.py
commit  b6fc3cf0046d3106e0dfb30f320d48514eff6fb2  2026-09-28
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**, and wider than Core's file: `btclib_ecc`'s
`curves/curve.py`, `curves/curve_group.py`, `curves/curve_group_2.py`,
`curves/curve_group_f.py` and `curves/sec_point.py` carry every curve
it has rather than secp256k1 alone. What the arithmetic is asserted
against is not a vector file but the `btclib_secp256k1` bindings, which
`curves.curve.mult` and its variants delegate to for secp256k1 and which
`btclib_ecc`'s own suite validates the Python arm against. Core's file
warns that it is slow and side-channel vulnerable; `btclib_ecc`'s
`SECURITY.md` publishes the same about its Python arm.

### `test/functional/test_framework/crypto/siphash.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/crypto/siphash.py
commit  af50ba8500a81e1a79cdf953d27bbf53ee6c979f  2026-07-17
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `hashes.siphash` takes the key words in the order
Core's own `siphash(k0, k1, data)` reads them out of a key
([ISS 373](https://github.com/btclib-org/btclib/issues/373)). Core's
second entry point, `siphash256`, is a little-endian `to_bytes` of a
`uint256` ahead of that same call, and `hashes.siphash`'s docstring is
where declining to restate that conversion is argued: a hash is already
bytes in that order in btclib.

### `test/functional/test_framework/descriptors.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/descriptors.py
commit  fab300b378941a233119805c0d62198596a57790  2025-12-26
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `descriptors.checksum`,
`descriptors.add_checksum` and `descriptors.strip_checksum` are
`descsum_polymod`, `descsum_expand`, `descsum_create` and
`descsum_check`. `drop_origins` has no equivalent: `descriptors.normalized`
is Core's `ToNormalizedString`, which re-roots each key at its last
hardened step, where dropping key origins is a different operation btclib
does not publish.

### `test/functional/test_framework/extendedkey.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/extendedkey.py
commit  d2a03d50acbf4bffc11048ef2cabb1b42ea78989  2026-06-19
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `bip32/` is BIP32 whole, where Core's file says of
itself that it provides "only basic functionality", and `slip132`,
`bip44`, `bip85` and `bip32/key_origin.py` stand beside it.

### `test/functional/test_framework/ipc_util.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/ipc_util.py
commit  858814146dd2ee17b2dda8ad01f50257affa23f5  2026-08-28
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. Cap'n Proto IPC into a `bitcoin-node`
process. `btclib` names it nowhere.

### `test/functional/test_framework/key.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/key.py
commit  00d0c5107b92c8972ab106c680579e06fd4fb100  2026-09-09
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `ecc/dsa.py` and `ecc/ssa.py` sign and verify,
`ecc/rfc6979_nonce.py` and `ecc/bip340_nonce.py` derive the nonces,
`key.py` holds the key objects Core's `ECKey` and `ECPubKey` are, and
`hashes.tagged_hash` is `TaggedHash`. What the signatures are asserted
against is BIP340's own vectors and the `btclib_secp256k1` bindings.

### `test/functional/test_framework/mempool_util.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/mempool_util.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. `fill_mempool` is ported, in
`src/bitcoin_node_tests/mempool_util.py`, over a throwaway `MiniWallet`
from `mini_wallet.py`
([ISS bitcoin-node-tests#70](https://github.com/btclib-org/bitcoin-node-tests/issues/70)).
`tx_in_orphanage` is `tests/integration/rpc_orphans_test.py`'s own
`in_orphanage`, and `create_large_orphan` is
`tests/integration/p2p_orphan_handling_test.py`'s own `_large_orphan`,
and `assert_mempool_contents` is
`tests/integration/mempool_package_rbf_test.py`'s own
`_assert_mempool_contents`.

### `test/functional/test_framework/messages.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/messages.py
commit  e3b026bf56e66baa6e070a00c136da95f3a16ef8  2026-07-07
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `p2p/` publishes one `Payload` subclass
per command over `tx/`, `block/`, `var_int`, `var_bytes`, `hashes`,
`block/partial_merkle_tree.py` and `p2p/merkleblock.py`; the
`C`-prefixed structures Core's file also carries are `tx/` and `block/`
in btclib. `filterload`, `filteradd` and `filterclear` are left out for
good by [ISS 1120](https://github.com/btclib-org/btclib/issues/1120): a
client constructs those to ask a node for the service that leaks its
wallet to that node, and BIP157 is what replaced them.

### `test/functional/test_framework/netutil.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/netutil.py
commit  59ebf558f3458bbc9038c7bf2958f2f224485ee1  2026-09-02
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. Interfaces, sockets and kernel inode
tables. `btclib` imports `socket` nowhere.

### `test/functional/test_framework/p2p.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/p2p.py
commit  e4d80e7001e9996a2836225f45a905dd16ffc777  2026-08-18
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. The envelope is `p2p/message.py`:
`Message.parse` reads one message off a stream and answers "not enough
bytes yet" as `IncompleteMessageError`, distinctly from a wrong
checksum, rewinding the stream to where it started.
`P2PConnection`, `P2PInterface`, `NetworkThread`, `P2PDataStore` and the
listener are the socket, the event loop and the peer state machine, and
are tf2's.

### `test/functional/test_framework/psbt.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/psbt.py
commit  a2a2b1745f0818364dd8149161e88cea1475d9b6  2026-05-27
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `psbt/` -- `Psbt`, `PsbtIn`, `PsbtOut`,
`psbt_view`, `psbt_size`, `musig2` and `silent_payments` -- where Core's
file is a reader and a writer of the maps.

### `test/functional/test_framework/script.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/script.py
commit  3fd68a95e68b4c6f3bb6c59d41dd196001110f3a  2026-04-07
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `script/script.py` is the codec,
`script/engine/` the execution, `script/op_codes_tapscript.py` and
`script/taproot.py` the taproot half, and `script/sig_hash.py` the
signature hashes Core's file also carries.

### `test/functional/test_framework/script_util.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/script_util.py
commit  3fd68a95e68b4c6f3bb6c59d41dd196001110f3a  2026-04-07
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `script/script_pub_key.py` publishes the
`ScriptPubKey` constructors Core's `*_script` functions are, with the
`assert_*` and `is_*` pair beside them, `type_and_payload` and
`address`. `bulk_vout` and `build_malleated_tx_package` build a
transaction of a chosen size or a package of a chosen shape for a node
to accept or refuse, and are tf2's.

### `test/functional/test_framework/segwit_addr.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/segwit_addr.py
commit  fe5e495c31de47b0ec732b943db11fe345d874af  2021-03-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `bech32.py` is the codec with no bitcoin in it and
`b32.py` the bitcoin semantics on top, which is the split this file does
not make.

### `test/functional/test_framework/signet.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/signet.py
commit  9b37d42b23be096cc4cfb457f1022e443102b650  2026-09-11
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**. `message_start` is BIP325's rule for a signet's
p2p magic: the challenge script, serialized with its CompactSize length,
SHA256d, then truncated to the magic's own width.
`bitcoin_core_rpc.magic_from_signet_challenge` is that same derivation,
and its own docstring states the rule in the same words Core's function
implements. `DEFAULT_SIGNET_CHALLENGE` there is Core's own
`SIGNET_DEFAULT_CHALLENGE` -- both constants compare equal, byte for
byte -- and `magic_from_chain("signet")` is the constant table entry
`SigNetParams` in Core's `chainparams.cpp` sets from exactly this
derivation, so the constant and the derivation are cross-checked against
each other rather than one merely standing in for the other.

This file's first and only revision is 2026-09-11
([ISS btclib-org/btclib#1751](https://github.com/btclib-org/btclib/issues/1751)'s
finding): the directory read this ledger's move brings from the start is
what would have caught it, over the days between its landing upstream
and this ledger's own move.

### `test/functional/test_framework/socks5.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/socks5.py
commit  4e8c4bc794c045beb678854e6e326fc04322c7c3  2026-08-04
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. A SOCKS5 server for the Tor tests.
`btclib` names SOCKS nowhere; `socks5.py`'s `Socks5Proxy` is this
repository's.

### `test/functional/test_framework/test_framework.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/test_framework.py
commit  3cb91bc7da67158fe6dc79886239f867245f1158  2026-10-06
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. The base class every functional test
derives from.

### `test/functional/test_framework/test_node.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/test_node.py
commit  a4bc96966faa9efcd7b387907d51b4ac53f7039d  2026-09-29
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. It starts, stops and drives a `bitcoind`,
and wraps `bitcoin-cli`.

### `test/functional/test_framework/test_shell.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/test_shell.py
commit  fa5f29774872d18febc0df38831a6e45f3de69cc  2025-12-16
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. The framework driven from a python shell.

### `test/functional/test_framework/util.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/util.py
commit  a4bc96966faa9efcd7b387907d51b4ac53f7039d  2026-09-29
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `fee.fee_from_vsize` over a `FeeRate` is
what `get_fee` computes, and what `satoshi_round` quantizes to is what
`amount.py`'s `valid_btc_amount`, `sats_from_btc` and `btc_from_sats`
work in; `util_xor` went to tf2 with the compressor by
ISS btclib-org/btclib#1123. The rest is the harness: the assertions,
the ports, the datadirs, the cookie files, the configuration files and
the waits.

### `test/functional/test_framework/v2_p2p.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/v2_p2p.py
commit  6a129983c9bf8efa1081f9a8b462c3635d1cfb39  2026-06-04
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**. ISS btclib-org/btclib#1066 put BIP324's
transport on tf2's side. Its non-cipher halves are btclib's:
`ecc/ellswift.py` is the key exchange and `kdf.hkdf` the key schedule.

### `test/functional/test_framework/wallet.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/wallet.py
commit  91586f701e1ebb12d8147feda7e78169a05da36f  2026-07-01
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. `MiniWallet` spends against a node's
chain. Its building blocks are `btclib-wallet`'s -- `tx_builder.build_psbt`,
`coin_selection`, `psbt_signer` and `btclib`'s `script/script_pub_key.py`
-- so it is tf2 written on those packages rather than a gap in either.

### `test/functional/test_framework/wallet_util.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/wallet_util.py
commit  42330922dd8d5f96dbc0cc6a8e4092500029f89d  2026-05-27
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `tx.input_weight` is
`calculate_input_weight`
([ISS 1067](https://github.com/btclib-org/btclib/issues/1067)), and
`b58.wif_from_prv_key` is `bytes_to_wif`. `get_generate_key`,
`test_address` and `WalletUnlock` need a node.

## The files that are not Python

The directory also carries `bip340_test_vectors.csv`,
`crypto/ellswift_decode_test_vectors.csv` and
`crypto/xswiftec_inv_test_vectors.csv`. Those are Core's copies of
bitcoin/bips files, and btclib vendors the bips originals instead, each
pinned against bitcoin/bips in its own `tests/_data/README.md`. No entry
above pins Core's copy, on purpose: pinning a copy of an upstream makes a
record drift for a reason that is not its subject's.

## The per-test ledger

Rule 5 of [ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220):
"The ledger gains a second table in tf2: one row per Core test, pinned,
with its verdict on each node." This is that table -- Core's own
functional tests, `test/functional/*.py`, each pinned the way the ledger
above pins a framework file, and each given one verdict per node this
repository's adapter reaches.

A verdict is **pass**; **fail**, naming the issue a disagreement is
filed as on `btclib-node`'s own tracker (rule 3); or **skip**, naming
the capability ([`capability.py`](./src/bitcoin_node_tests/capability.py))
the node does not declare; or **not ported**, where the node declares
every capability the row asks for and the test run against it is still
a stub ending in `pytest.fail`
([ISS 82](https://github.com/btclib-org/bitcoin-node-tests/issues/82)).
bitcoind is the oracle (rule 3): a **fail** on bitcoind is this
repository's own defect rather than a finding for another tracker.

A row whose subject is bitcoind's own option carries **bitcoind only**
in its `btclib-node` column instead: not a verdict on that node, since
no test of this shape ever runs against one. `capability.py`'s own
module docstring is the one place that states which options this
covers, and does not decide it row by row here.

A `btclib-node` cell gives the verdict of each build the latest
`node-integration.yml` run on `main` measures: the PyPI release and
btclib-node's own `main`. Where they agree, the cell is that verdict
alone. Where they differ, the cell reads `<verdict> on the build;
<verdict> on a build past [ISS ...]`: the release's first, then `main`'s,
the issue being the one whose fix `main` carries. A cell keeps no verdict
of an older build; git holds the history.
`.github/scripts/btclib_node_verdict.py` compares each cell with both runs.

A `fail` names the issue it is filed as. A test whose call ended and
whose teardown then timed out is not a `fail` on that account: the script
lists it under a heading of its own
([ISS btclib-node#1274](https://github.com/btclib-org/btclib-node/issues/1274)).

A `bitcoind` cell can be build-dependent the same way, for a fact of
the pinned release's own binary that another build of bitcoind answers
differently -- `capability.py`'s own module docstring is the one rule
this covers, stated once rather than repeated per row: the class says
what every build of a node can do, and a fact that varies release to
release of the *same* binary is read from the one under test instead of
fixed for the whole verdict. `feature_torcontrol.py`'s and
`p2p_bip434_feature.py`'s own rows below are this table's own instances
of it.

A pin or date cell reading **same** repeats the pin and date of the
nearest row above it that names the same Core test file, the row width
leaving no room to write them again.

This table is not read by `.github/scripts/check_vendored_vectors.py`:
that script's own docstring says so -- "this tree carrying no second
ledger" -- and it reads `test/functional/test_framework/` alone, the
directory the ledger above pins. A pin here is re-checked the same way,
by hand:

```shell
entry_path=test/functional/<test>.py
gh api --method GET repos/bitcoin/bitcoin/commits \
    -f "path=${entry_path:?}" -f per_page=1 \
    --jq '.[0].sha + "  " + .[0].commit.committer.date[:10]'
```

| Core test | pin | read at | bitcoind | btclib-node |
| --- | --- | --- | --- | --- |
| `feature_blocksdir.py` | `0d1301b47a35` | 2026-03-24 | pass | skip (blk) |
| `feature_filelock.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `rpc_whitelist.py` | `fa24693819e0` | 2026-05-26 | pass | pass |
| `rpc_users.py` | `faf993ee4421` | 2026-05-26 | pass | pass |
| `rpc_users.py` (`-norpcauth`) | same | same | pass | pass |
| `rpc_users.py` (`-rpcuser`/`-rpcpassword`) | same | same | pass | pass |
| `rpc_users.py` (`-norpccookiefile`) | same | same | pass | pass |
| `p2p_block_sync.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `p2p_compactblocks_hb.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `p2p_getdata.py` | `aaf941202667` | 2026-07-31 | pass | pass |
| `p2p_invalid_locator.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `p2p_invalid_messages.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_invalid_messages.py` (log) | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `p2p_invalid_messages.py` (inv, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (inv, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (getdata, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (getdata, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (headers, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (headers, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (invalid pow, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (invalid pow, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (size, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (size, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (dup version, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (dup version, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (checksum, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (checksum, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (msgtype, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (msgtype, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 empty, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 empty, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 no addr, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 no addr, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 long, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 long, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 net id, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 net id, log) | same | same | pass | skip |
| `p2p_leak.py` (wire) | `36775471f81a` | 2026-09-09 | pass | pass |
| `p2p_leak.py` (log) | same | same | pass | skip |
| `p2p_leak.py` (version boundary) | same | same | pass | pass |
| `p2p_handshake.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_handshake.py` (log) | same | same | pass | skip |
| `p2p_handshake.py` (services, wire) | same | same | pass | skip |
| `p2p_handshake.py` (services, log) | same | same | pass | skip |
| `p2p_handshake.py` (limited, wire) | same | same | pass | skip |
| `p2p_handshake.py` (limited, log) | same | same | pass | skip |
| `p2p_handshake.py` (feeler, wire) | same | same | pass | skip |
| `p2p_handshake.py` (feeler, log) | same | same | pass | skip |
| `p2p_handshake.py` (self, wire) | same | same | pass | skip |
| `p2p_handshake.py` (self, log) | same | same | pass | skip |
| `p2p_addr_relay.py` (wire) | `b7211ba80cde` | 2026-09-22 | pass | pass |
| `p2p_addr_relay.py` (log) | same | same | pass | skip |
| `p2p_addrv2_relay.py` (wire) | `fa5f29774872` | 2025-12-16 | pass | pass |
| `p2p_addrv2_relay.py` (log) | same | same | pass | skip |
| `p2p_net_deadlock.py` | `a0473442d1c2` | 2024-07-16 | pass | skip (raw_msg) |
| `feature_uacomment.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `rpc_uptime.py` | `406c2348ddbf` | 2026-06-13 | pass, the mock clock followed or not per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (clock) |
| `feature_torcontrol.py` | `4556ef626754` | 2026-09-15 | pass, the `PoWDefensesEnabled` flag asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `p2p_bip434_feature.py` | `da74ff9ca49e` | 2026-06-04 | pass, `FEATURE`'s own disconnects asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `feature_framework_miniwallet.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | pass |
| `feature_framework_miniwallet.py` (`confirmed_only`) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (generate) |
| `feature_framework_miniwallet.py` (`fee_rate`) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (datacarrier) |
| `feature_framework_miniwallet.py` (TRUC) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (datacarrier) |
| `mempool_resurrect.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `mempool_spend_coinbase.py` | `6eca11175be6` | 2026-07-16 | pass | pass |
| `feature_dersig.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_dersig.py` (wire) | same | same | pass | skip |
| `feature_dersig.py` (log) | same | same | pass | skip |
| `feature_dersig.py` (signature) | same | same | pass | skip |
| `feature_cltv.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_cltv.py` (wire) | same | same | pass | skip |
| `feature_cltv.py` (log) | same | same | pass | skip |
| `feature_cltv.py` (failures, activation) | same | same | pass | skip |
| `feature_cltv.py` (failures, mempool) | same | same | pass | skip |
| `feature_cltv.py` (failures, block) | same | same | pass | pass |
| `feature_csv_activation.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_csv_activation.py` (lock times) | same | same | pass | skip |
| `feature_nulldummy.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `feature_dirsymlinks.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `feature_posix_fs_permissions.py` | [`3fd68a95e68b`](https://github.com/bitcoin/bitcoin/commit/3fd68a95e68b) | 2026-04-07 | pass | pass |
| `rpc_createmultisig.py` | `771200ca4362` | 2026-06-30 | pass | bitcoind only |
| `rpc_createmultisig.py` (spend) | same | same | pass, `combinerawtransaction`'s mergeability refusals asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (sign_raw_transaction) |
| `rpc_setban.py` (ban) | `fa21edddb272` | 2026-03-27 | pass | pass |
| `rpc_setban.py` (restart) | same | same | pass | skip (debug_log) |
| `rpc_setban.py` (noban) | same | same | pass | pass |
| `rpc_setban.py` (non-IP) | same | same | pass | pass |
| `rpc_setban.py` (bantime) | same | same | pass | pass |
| `p2p_disconnect_ban.py` (disconnectnode) | [`dcd90fbe54cf`](https://github.com/bitcoin/bitcoin/commit/dcd90fbe54cf) | 2026-04-07 | pass | pass |
| `mempool_datacarrier.py` | `fa5f29774872` | 2025-12-16 | pass, the policy asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `mempool_dust.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (dust_relay_fee) |
| `mempool_sigoplimit.py` | `5d25a0c28d19` | 2026-07-07 | pass | skip |
| `mempool_package_limits.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass; skip (limit_cluster_count) on a build before the cluster mempool | skip (limit_cluster_count) |
| `mempool_updatefromblock.py` | `fa6b05c96ffb` | 2026-03-12 | pass, the limits asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_leak_tx.py` (in block) | `fa5f29774872` | 2025-12-16 | pass, the `getpeerinfo` fields asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_leak_tx.py` (replaced) | same | same | pass | skip |
| `p2p_leak_tx.py` (unannounced) | same | same | pass | skip |
| `feature_utxo_set_hash.py` | `58eeab790d98` | 2026-05-13 | pass | pass |
| `rpc_getdescriptoractivity.py` | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `rpc_getdescriptoractivity.py` (mempool) | same | same | pass | skip |
| `rpc_getblockstats.py` | `b7cbd804284b` | 2026-05-25 | pass | skip (stats) |
| `feature_fastprune.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `rpc_scanblocks.py` | `aeca0610865e` | 2026-07-01 | pass | skip |
| `rpc_scanblocks.py` (no index) | same | same | pass | skip |
| `p2p_eviction.py` | `1b76e0473647` | 2026-07-24 | pass, `-maxconnections` read per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | pass |
| `feature_presegwit_node_upgrade.py` | [`fad7bd9ba3ee`](https://github.com/bitcoin/bitcoin/commit/fad7bd9ba3ee) | 2026-01-14 | pass, the refusal's leading `": "` asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (test_activation_height) |
| `rpc_validateaddress.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (validate_address) |
| `p2p_addrfetch.py` | [`3fd68a95e68b`](https://github.com/bitcoin/bitcoin/commit/3fd68a95e68b) | 2026-04-07 | pass | skip (typed_outbound) |
| `rpc_echo_payload.py` | [`fa7bc26d1276`](https://github.com/bitcoin/bitcoin/commit/fa7bc26d1276) | 2026-08-06 | pass, a connection per call on a libevent build ([ISS 415](https://github.com/btclib-org/bitcoin-node-tests/issues/415)) | skip (rpc_work_queue) |
| `p2p_compactblocks_blocksonly.py` | [`bf9884f4e55d`](https://github.com/bitcoin/bitcoin/commit/bf9884f4e55d) | 2026-06-18 | pass, the ignored `cmpctblock` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (blocks_only) |
| `rpc_getblockfilter.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (block_filter_index) |
| `rpc_getblockfrompeer.py` | [`779f4446803d`](https://github.com/bitcoin/bitcoin/commit/779f4446803d) | 2026-05-25 | pass | skip (block_from_peer) |
| `p2p_node_network_limited.py` | [`fa7bac94d87a`](https://github.com/bitcoin/bitcoin/commit/fa7bac94d87a) | 2026-03-12 | pass | skip (suspend_network) |
| `rpc_getdescriptorinfo.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass, the whitespace refusal's wording asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (descriptor_info) |
| `p2p_timeouts.py` (wire) | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (peer_timeout) |
| `p2p_timeouts.py` (log) | same | same | pass | skip (peer_timeout) |
| `p2p_timeouts.py` (refusal) | same | same | pass | skip (peer_timeout) |
| `p2p_ping.py` (wire) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (peer_timeout) |
| `p2p_ping.py` (log) | same | same | pass | skip (peer_timeout) |
| `mempool_expiry.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (mempool_expiry) |
| `p2p_add_connections.py` | [`4c79f3a34d00`](https://github.com/bitcoin/bitcoin/commit/4c79f3a34d00) | 2026-09-14 | pass | skip (typed_outbound) |
| `p2p_add_connections.py` (`manual`) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `feature_includeconf.py` (order) | [`fa71c15f8610`](https://github.com/bitcoin/bitcoin/commit/fa71c15f8610) | 2025-11-26 | pass | skip (ua_comment) |
| `feature_includeconf.py` (double negative) | same | same | pass | pass |
| `feature_includeconf.py` (`-includeconf`) | same | same | pass | pass |
| `feature_includeconf.py` (nested) | same | same | pass | pass |
| `feature_includeconf.py` (missing) | same | same | pass | pass |
| `feature_reindex_init.py` | [`0d1301b47a35`](https://github.com/bitcoin/bitcoin/commit/0d1301b47a35) | 2026-03-24 | pass, the refusal's leading `": "` asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)); skip (reindex_after_failure) on a build whose `-test` lacks the reindex value | skip (reindex_after_failure) |
| `rpc_generate.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (generate) |
| `rpc_signrawtransactionwithkey.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (sign_raw_transaction) |
| `rpc_scantxoutset.py` | [`b388674acf06`](https://github.com/bitcoin/bitcoin/commit/b388674acf06) | 2026-08-06 | pass, `start`'s refusal of a null scan-object list asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (scan_utxo_set) |
| `feature_proxy.py` | [`f82043af507a`](https://github.com/bitcoin/bitcoin/commit/f82043af507a) | 2026-06-30 | pass; skip (proxy_per_network) on a build whose `-help` shows no `-proxy` suffix, the malformed suffix starts' refusal asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (proxy) |
| `feature_proxy.py` (`-cjdnsreachable`) | same | same | pass | skip (cjdns) |
| `feature_proxy.py` (`-i2psam`) | same | same | pass | skip (i2p_sam) |
| `feature_proxy.py` (`-onlynet`) | same | same | pass | skip (onlynet) |
| `wallet_signmessagewithaddress.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_blank.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_coinbase_category.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `p2p_initial_headers_sync.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | pass |
| `p2p_initial_headers_sync.py` (stall, wire) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (stall, log) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (noban, wire) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (noban, log) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` | [`2fabbc0bb38d`](https://github.com/bitcoin/bitcoin/commit/2fabbc0bb38d) | 2026-09-09 | pass | skip (tx_reconciliation) |
| `p2p_sendtxrcncl.py` (bloom) | same | same | pass | skip (tx_reconciliation) |
| `p2p_sendtxrcncl.py` (outbound) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (outbound, log) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (blocksonly) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (off) | same | same | pass | pass |
| `p2p_sendtxrcncl.py` (off, log) | same | same | pass | skip (debug_log) |
| `p2p_sendtxrcncl.py` (violations, wire) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (violations, log) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (kept, wire) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` (kept, log) | same | same | pass | skip |
| `feature_reindex.py` (reindex) | [`9e6546c517cd`](https://github.com/bitcoin/bitcoin/commit/9e6546c517cd) | 2026-06-21 | pass | skip (reindex) |
| `feature_reindex.py` (out of order) | same | same | pass | skip (reindex) |
| `feature_reindex.py` (interrupted) | same | same | pass, the interruption's log line asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (reindex) |
| `feature_reindex_readonly.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (reindex) |
| `p2p_feefilter.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | pass |
| `p2p_feefilter.py` (forcerelay) | same | same | pass | pass |
| `p2p_feefilter.py` (filter) | same | same | pass | pass |
| `p2p_feefilter.py` (block-relay-only) | same | same | pass | skip |
| `p2p_feefilter.py` (blocksonly) | same | same | pass | skip |
| `p2p_mutated_blocks.py` (wire) | [`9c5dd2926aa9`](https://github.com/bitcoin/bitcoin/commit/9c5dd2926aa9) | 2026-06-18 | pass | skip |
| `p2p_mutated_blocks.py` (log) | same | same | pass | skip |
| `p2p_mutated_blocks.py` (missing parent, wire) | same | same | pass | pass |
| `p2p_mutated_blocks.py` (missing parent, log) | same | same | pass | skip |
| `feature_anchors.py` | [`ddf033054ff6`](https://github.com/bitcoin/bitcoin/commit/ddf033054ff6) | 2026-09-11 | pass, the network-off step asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `feature_anchors.py` (onion) | same | same | pass, the network-toggle steps asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_addr_selfannouncement.py` (inbound, wire) | [`dab7f2c984bd`](https://github.com/bitcoin/bitcoin/commit/dab7f2c984bd) | 2026-07-07 | pass, the first address message asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_addr_selfannouncement.py` (inbound, log) | same | same | pass, the first address message asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_addr_selfannouncement.py` (outbound, wire) | same | same | pass | skip |
| `p2p_addr_selfannouncement.py` (outbound, log) | same | same | pass | skip |
| `p2p_addr_selfannouncement.py` (`-onlynet`) | same | same | pass, the onion `-externalip` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_message_capture.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (capture_messages) |
| `feature_blocksxor.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (blocks_xor) |
| `feature_remove_pruned_files_on_startup.py` | [`fa9aced8006b`](https://github.com/bitcoin/bitcoin/commit/fa9aced8006b) | 2025-01-22 | pass | skip (fastprune) |
| `wallet_createwalletdescriptor.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_sendmany.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_timelock.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_simulaterawtx.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_rescan_unconfirmed.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_miniscript_decaying_multisig_descriptor_psbt.py` | [`88f802983571`](https://github.com/bitcoin/bitcoin/commit/88f802983571) | 2026-01-31 | pass | skip (node_wallet) |
| `wallet_anchor.py` | [`609d265ebc51`](https://github.com/bitcoin/bitcoin/commit/609d265ebc51) | 2025-09-03 | pass | skip (node_wallet) |
| `wallet_disable.py` | [`3fd68a95e68b`](https://github.com/bitcoin/bitcoin/commit/3fd68a95e68b) | 2026-04-07 | pass | bitcoind only |
| `mempool_accept_wtxid.py` | [`3f5211cba8e7`](https://github.com/bitcoin/bitcoin/commit/3f5211cba8e7) | 2026-01-21 | pass | pass |
| `rpc_orphans.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | pass |
| `mining_template_verification.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (block_proposal) |
| `p2p_i2p_ports.py` | [`fa20275db32c`](https://github.com/bitcoin/bitcoin/commit/fa20275db32c) | 2025-10-21 | pass | skip (i2p_sam) |
| `p2p_i2p_sessions.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass, the session lines' wording asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (i2p_sam) |
| `p2p_dns_seeds.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (dns_seed) |
| `p2p_seednode.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (address_fetch) |
| `p2p_ibd_stalling.py` (wire) | [`24628d3ae7dc`](https://github.com/bitcoin/bitcoin/commit/24628d3ae7dc) | 2026-09-14 | pass | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (log) | same | same | pass, `Stall started`'s absence once the block withheld first is sent asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (`manual`, wire) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (`manual`, log) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_private_broadcast.py` | [`ac6b6c1f06e9`](https://github.com/bitcoin/bitcoin/commit/ac6b6c1f06e9) | 2026-08-18 | pass, the refusals without `-privatebroadcast` and `attempts_remaining` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (private_broadcast) |
| `p2p_tx_download.py` (expiry) | [`1278a5970d5a`](https://github.com/bitcoin/bitcoin/commit/1278a5970d5a) | 2026-08-06 | pass | skip (clock) |
| `p2p_tx_download.py` (disconnect) | same | same | pass | pass |
| `p2p_tx_download.py` (notfound) | same | same | pass | pass |
| `p2p_tx_download.py` (tiebreak) | same | same | pass | skip (typed_outbound) |
| `p2p_tx_download.py` (inbound) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (outbound) | same | same | pass | skip (typed_outbound) |
| `p2p_tx_download.py` (noban) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (txid) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (txid beside wtxid) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (large inv) | same | same | pass | pass |
| `p2p_tx_download.py` (duplicate inv) | same | same | pass, the duplicates asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (debug_log) |
| `p2p_tx_download.py` (spurious notfound) | same | same | pass | pass |
| `p2p_tx_download.py` (in flight) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (inv block) | same | same | pass, `inv_to_send` asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (clock) |
| `p2p_tx_download.py` (tx requests) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (rejects) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (mismatch) | same | same | pass | skip (clock) |
| `p2p_blocksonly.py` (`-blocksonly`, wire) | [`278710a88d8f`](https://github.com/bitcoin/bitcoin/commit/278710a88d8f) | 2026-06-17 | pass | skip |
| `p2p_blocksonly.py` (`-blocksonly`, log) | same | same | pass | skip |
| `p2p_blocksonly.py` (block-relay-only, wire) | same | same | pass | skip |
| `p2p_blocksonly.py` (block-relay-only, log) | same | same | pass | skip |
| `p2p_orphan_handling.py` (arrival timing) | [`9cc7dc50bdc9`](https://github.com/bitcoin/bitcoin/commit/9cc7dc50bdc9) | 2026-08-17 | pass | skip |
| `p2p_orphan_handling.py` (rejected parents) | same | same | pass | skip |
| `p2p_orphan_handling.py` (multiple parents) | same | same | pass | skip |
| `p2p_orphan_handling.py` (overlapping parents) | same | same | pass | skip |
| `p2p_orphan_handling.py` (orphan of orphan) | same | same | pass | skip |
| `p2p_orphan_handling.py` (parent confirmed) | same | same | pass, the reconsideration asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_orphan_handling.py` (inherit rejection) | same | same | pass | skip |
| `p2p_orphan_handling.py` (same txid) | same | same | pass | skip |
| `p2p_orphan_handling.py` (same txid parent) | same | same | pass | skip |
| `p2p_orphan_handling.py` (txid inv) | same | same | pass | skip |
| `p2p_orphan_handling.py` (prefer outbound) | same | same | pass | skip |
| `p2p_orphan_handling.py` (announcers) | same | same | pass | skip |
| `p2p_orphan_handling.py` (parents change) | same | same | pass | skip |
| `p2p_orphan_handling.py` (maximal package) | same | same | pass | skip |
| `p2p_compactblocks.py` (sendcmpct) | [`28641fd195db`](https://github.com/bitcoin/bitcoin/commit/28641fd195db) | 2026-07-31 | pass | pass |
| `p2p_compactblocks.py` (construction) | same | same | pass | pass |
| `p2p_compactblocks.py` (requests) | same | same | pass | pass |
| `p2p_compactblocks.py` (getblocktxn requests) | same | same | pass | pass |
| `p2p_compactblocks.py` (getblocktxn handler) | same | same | pass | pass |
| `p2p_compactblocks.py` (not at tip) | same | same | pass | pass |
| `p2p_compactblocks.py` (low work, wire) | same | same | pass | pass |
| `p2p_compactblocks.py` (low work, log) | same | same | pass | skip |
| `p2p_compactblocks.py` (incorrect blocktxn) | same | same | pass | pass |
| `p2p_compactblocks.py` (end to end) | same | same | pass | pass |
| `p2p_compactblocks.py` (invalid tx) | same | same | pass | pass |
| `p2p_compactblocks.py` (empty getblocktxn, wire) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | pass |
| `p2p_compactblocks.py` (empty getblocktxn, log) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_compactblocks.py` (multiple blocktxn, wire) | same | same | pass | pass |
| `p2p_compactblocks.py` (multiple blocktxn, log) | same | same | pass | skip |
| `p2p_compactblocks.py` (invalid sendcmpct, wire) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | pass |
| `p2p_compactblocks.py` (invalid sendcmpct, log) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_compactblocks.py` (invalid cmpctblock) | same | same | pass | pass |
| `p2p_compactblocks.py` (sendcmpct, outbound) | same | same | pass | skip |
| `p2p_compactblocks.py` (stalling peer) | same | same | pass | pass |
| `p2p_compactblocks.py` (parallel reconstruction) | same | same | pass | skip |
| `p2p_compactblocks.py` (high-bandwidth states) | same | same | pass | pass |
| `p2p_compactblocks.py` (ignored) | same | same | pass, the ignored `cmpctblock` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | fail ([ISS btclib-node#1890](https://github.com/btclib-org/btclib-node/issues/1890)) on the build; pass on a build past [ISS btclib-node#1897](https://github.com/btclib-org/btclib-node/issues/1897) |
| `feature_startupnotify.py` | [`fa71c15f8610`](https://github.com/bitcoin/bitcoin/commit/fa71c15f8610) | 2025-11-26 | pass | skip (startup_notify) |
| `rpc_dumptxoutset.py` | [`58eeab790d98`](https://github.com/bitcoin/bitcoin/commit/58eeab790d98) | 2026-05-13 | pass, the dump at a forked height asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (dump_utxo_set) |
| `feature_loadblock.py` | [`fa4fc8c1d7b5`](https://github.com/bitcoin/bitcoin/commit/fa4fc8c1d7b5) | 2026-05-22 | pass | skip (load_block) |
| `feature_port.py` | [`997757dd2b4d`](https://github.com/bitcoin/bitcoin/commit/997757dd2b4d) | 2024-11-15 | pass | skip (debug_log) |
| `p2p_opportunistic_1p1c.py` (parent first) | [`0bd3d3dfa562`](https://github.com/bitcoin/bitcoin/commit/0bd3d3dfa562) | 2026-07-24 | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent first, P2PK) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (child first) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (low, high child) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (low, high, P2PK) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (orphan invalid) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent invalid) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (multiple parents) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent in mempool) | same | same | pass, the package asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_opportunistic_1p1c.py` (1p1c on 1p1c) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (DoS, large orphans) | same | same | pass, the eviction asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_opportunistic_1p1c.py` (DoS, many orphans) | same | same | pass, the orphanage asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip |
| `p2p_block_times.py` | [`5d5397d84108`](https://github.com/bitcoin/bitcoin/commit/5d5397d84108) | 2026-07-25 | pass, `last_block_announcement` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_outbound_eviction.py` (unprotected) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip |
| `p2p_outbound_eviction.py` (protected) | same | same | pass | skip |
| `p2p_outbound_eviction.py` (mixed) | same | same | pass | skip |
| `p2p_outbound_eviction.py` (block-relay-only) | same | same | pass | skip |
| `p2p_tx_privacy.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | pass |
| `p2p_invalid_block.py` (wire) | [`fa16bc53d79c`](https://github.com/bitcoin/bitcoin/commit/fa16bc53d79c) | 2026-04-16 | pass | skip (clock) |
| `p2p_invalid_block.py` (log) | same | same | pass | skip (clock) |
| `feature_maxtipage.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (max_tip_age) |
| `p2p_blockfilters.py` | [`3fd68a95e68b`](https://github.com/bitcoin/bitcoin/commit/3fd68a95e68b) | 2026-04-07 | pass | skip (peer_block_filters) |
| `p2p_getaddr_caching.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (known_addresses) |
| `mempool_reorg.py` (coinbase) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (invalidate_block) |
| `mempool_reorg.py` (relay) | same | same | pass | skip (clock) |
| `interface_rpc.py` (getrpcinfo) | [`fa2bd96cc0d4`](https://github.com/bitcoin/bitcoin/commit/fa2bd96cc0d4) | 2026-08-06 | pass | skip (rpc_info) |
| `interface_rpc.py` (batch) | same | same | pass | pass |
| `interface_rpc.py` (status codes) | same | same | pass | pass |
| `interface_rpc.py` (notifications) | same | same | pass | skip (generate) |
| `interface_rpc.py` (work queue) | same | same | pass | skip (rpc_work_queue) |
| `p2p_ibd_txrelay.py` (wire) | [`fab352053d6e`](https://github.com/bitcoin/bitcoin/commit/fab352053d6e) | 2026-04-16 | pass, the old block's coinbase asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (clock) |
| `p2p_ibd_txrelay.py` (log) | same | same | pass, the old block's coinbase asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (clock) |
| `feature_bip68_sequence.py` | [`ab41492c6ba7`](https://github.com/bitcoin/bitcoin/commit/ab41492c6ba7) | 2026-01-09 | pass | skip (test_activation_height) |
| `mempool_accept.py` | [`eaef8d31118d`](https://github.com/bitcoin/bitcoin/commit/eaef8d31118d) | 2026-07-07 | pass, `vsize_adjusted` and `vsize_bip141` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)), the null-data and bare-multisig checks per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | fail ([ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334)) on the build; pass on a build past [ISS btclib-node#1889](https://github.com/btclib-org/btclib-node/issues/1889) |
| `mempool_cluster.py` | [`659671ac3db7`](https://github.com/bitcoin/bitcoin/commit/659671ac3db7) | 2026-06-04 | pass; skip (limit_cluster_size) on a build before the cluster mempool | skip (limit_cluster_size) |
| `feature_minchainwork.py` | [`c502b65c007b`](https://github.com/bitcoin/bitcoin/commit/c502b65c007b) | 2026-10-03 | pass | skip (minimum_chain_work) |
| `feature_minchainwork.py` (outbound) | same | same | pass | skip |
| `mempool_packages.py` | [`6f113cb1847c`](https://github.com/bitcoin/bitcoin/commit/6f113cb1847c) | 2026-02-09 | pass, the limits asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (mempool_graph) |
| `feature_versionbits_warning.py` | [`5bd990a3ddb1`](https://github.com/bitcoin/bitcoin/commit/5bd990a3ddb1) | 2026-06-03 | pass, the reserved bit asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (alert_notify) |
| `mempool_package_rbf.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass, the replacement limit asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | fail ([ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334)) on the build; skip (maxmempool) on a build past [ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334) |
| `p2p_headers_sync_with_minchainwork.py` | [`ff3e2e4ebdce`](https://github.com/bitcoin/bitcoin/commit/ff3e2e4ebdce) | 2026-08-19 | pass | skip (minimum_chain_work) |
| `p2p_unrequested_blocks.py` | [`fab352053d6e`](https://github.com/bitcoin/bitcoin/commit/fab352053d6e) | 2026-04-16 | pass | skip (minimum_chain_work) |
| `p2p_1p1c_network.py` | [`95ef0fc5e781`](https://github.com/bitcoin/bitcoin/commit/95ef0fc5e781) | 2025-12-29 | pass, the fees asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | pass |
| `mempool_ephemeral_dust.py` | [`7c8030143925`](https://github.com/bitcoin/bitcoin/commit/7c8030143925) | 2026-02-25 | pass, `test_non_truc` asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | skip (generate) |
| `mempool_ephemeral_dust.py` (nonzero dust) | same | same | pass | pass |
| `mempool_ephemeral_dust.py` (reorg) | same | same | pass, the reorg asserted per-build ([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)) | pass |
| `feature_notifications.py` (`-blocknotify`) | [`469b0e59a29a`](https://github.com/bitcoin/bitcoin/commit/469b0e59a29a) | 2026-09-01 | pass | skip (block_notify) |
| `feature_notifications.py` (`-alertnotify`) | same | same | pass, the warning's wording asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (alert_notify) |
| `feature_notifications.py` (`-shutdownnotify`) | same | same | pass | skip |
| `feature_settings.py` | [`0654511e1b93`](https://github.com/bitcoin/bitcoin/commit/0654511e1b93) | 2026-06-17 | pass | skip (settings_file) |
| `rpc_getchaintips.py` | [`fa16bc53d79c`](https://github.com/bitcoin/bitcoin/commit/fa16bc53d79c) | 2026-04-16 | pass | skip (generate) |
| `rpc_preciousblock.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (precious_block) |
| `rpc_invalidateblock.py` | [`fab352053d6e`](https://github.com/bitcoin/bitcoin/commit/fab352053d6e) | 2026-04-16 | pass, the ancestors' check run per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (generate) |
| `rpc_signmessagewithprivkey.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (sign_message_with_privkey) |
| `feature_chain_tiebreaks.py` | [`20ae9b98eab2`](https://github.com/bitcoin/bitcoin/commit/20ae9b98eab2) | 2026-03-04 | pass, the restart's tip check run per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (invalidate_block) |
| `p2p_sendheaders.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (generate) |
| `p2p_fingerprint.py` | [`fa16bc53d79c`](https://github.com/bitcoin/bitcoin/commit/fa16bc53d79c) | 2026-04-16 | pass | skip (clock) |
| `rpc_estimatefee.py` | [`4056908f0fea`](https://github.com/bitcoin/bitcoin/commit/4056908f0fea) | 2026-09-29 | pass, the `options` checks and the estimator refusal run per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (estimate_smart_fee) |
| `feature_assumevalid.py` | [`fa16bc53d79c`](https://github.com/bitcoin/bitcoin/commit/fa16bc53d79c) | 2026-04-16 | pass, its log lines read per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (assume_valid) |
| `feature_rbf.py` | [`1a85ca1dff1f`](https://github.com/bitcoin/bitcoin/commit/1a85ca1dff1f) | 2026-04-24 | pass, the replacement rules' wording asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (incremental_relay_fee) |
| `p2p_permissions.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (peer_permissions) |
| `p2p_private_broadcast_retry_v1.py` | [`4e8c4bc794c0`](https://github.com/bitcoin/bitcoin/commit/4e8c4bc794c0) | 2026-08-04 | pass | skip (private_broadcast) |
| `p2p_private_broadcast_cap.py` | [`82a02a2a2208`](https://github.com/bitcoin/bitcoin/commit/82a02a2a2208) | 2026-07-07 | pass, the cap asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (private_broadcast) |
| `rpc_net.py` (`addnode`) | [`71c30b608382`](https://github.com/bitcoin/bitcoin/commit/71c30b608382) | 2026-09-22 | pass, the blank address refusal asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (proxy) |
| `rpc_net.py` (service flags) | same | same | pass | skip (proxy) |
| `rpc_net.py` (`getnodeaddresses`) | same | same | pass | skip (proxy) |
| `rpc_net.py` (`addpeeraddress`) | same | same | pass, the blank address refusal asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (known_addresses) |
| `rpc_net.py` (`getaddrmaninfo`) | same | same | pass | skip (cjdns) |
| `rpc_net.py` (`getrawaddrman`) | same | same | pass | skip (cjdns) |
| `feature_config_args.py` (`-proxy`) | [`2630d8e6c9d6`](https://github.com/bitcoin/bitcoin/commit/2630d8e6c9d6) | 2026-09-22 | pass | skip (proxy) |
| `feature_config_args.py` (`-connect`) | same | same | pass | skip (proxy) |
| `feature_config_args.py` (`-privatebroadcast`) | same | same | pass, the warning's last sentence asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (proxy) |

Each line gives the reason for a file's `btclib-node` cell and, where there is
one, the issue it is filed as. What differs from Core's file is in the
docstrings of `tests/integration/<file>*_test.py`. The cell gives the verdict
per build; an entry gives the reason only. A row with no entry here has its
prose in the later sections.

- `feature_blocksdir.py`: a smaller claim, Core also mining before its disk
  read. Skips on `blk_files`: btclib-node keeps its own block format, by
  decision
  ([ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)).
  The refusal is matched on the node's whole stderr
  ([ISS 19](https://github.com/btclib-org/bitcoin-node-tests/issues/19)).
- `feature_filelock.py`: a smaller claim: the cookie- and PID-file checks and
  the wallet-directory lock are dropped. btclib-node writes Core's lock error
  ([ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147)).
- `rpc_whitelist.py`: a smaller claim: named users, not Core's `strange_users`
  roster. Gated on `rpc_auth_config`
  ([ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)).
- `rpc_users.py`: a smaller claim: no Windows branch, no bare `-rpcauth`, no
  `share/rpcauth` script. `-norpcauth` is gated on `rpc_auth_negation`
  ([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176));
  `-rpcuser`, `-rpcpassword` and `-norpccookiefile` run through `rpc_auth`
  ([ISS 34](https://github.com/btclib-org/bitcoin-node-tests/issues/34)). A
  cookie that cannot be written and a malformed `-rpcauth` are refused in Core's
  `Unable to start HTTP server` wording
  ([ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210)).
- `p2p_getdata.py`: a smaller claim: the later `getdata` is asked of genesis,
  not of a mined tip, `MINE` not being every node's fact
  ([ISS 2](https://github.com/btclib-org/bitcoin-node-tests/issues/2),
  [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)).
- `p2p_block_sync.py`: Core's claim in full. Skips on `mine` where undeclared.
- `p2p_invalid_locator.py`: Core's claim in full. Skips on `mine` where
  undeclared.
- `p2p_compactblocks_hb.py`: Core's claim in full, its peers told apart by
  connection order, not by `-uacomment`.
- `p2p_net_deadlock.py`: Core's claim in full. Skips on `raw_message`, Core's
  `sendmsgtopeer`.
- `p2p_leak.py`: a wire row and a log row per Core check
  ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)). The
  checks before the handshake completes are not ported: they ask what a node
  sends, not what it logs. The version boundary (bitcoin/bitcoin#36152) is wire
  only.
- `p2p_invalid_messages.py`: a wire row and a log row per Core assertion
  ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)): magic,
  size, oversized `inv`, `getdata` and headers, invalid proof of work, duplicate
  `version`, checksum, message type and the `addrv2` checks. The log rows skip
  on `debug_log`. Core's whitelist permission is dropped: it grants `Addr`, not
  `NoBan`. The `addrv2` rows rely on a peer's messages being handled in order
  ([ISS btclib-node#1739](https://github.com/btclib-org/btclib-node/issues/1739)).
- `p2p_handshake.py`: the redundant-`verack` check, a wire row and a log row
  ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)). The
  other rows are in *Outbound connections* below.
- `p2p_addr_relay.py`: the first check of Core's `run_test`, a wire row and a
  log row ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)).
- `p2p_addrv2_relay.py`: the first check of Core's `run_test`, a wire row and a
  log row ([ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)).
- `p2p_bip434_feature.py`: narrowed to the disconnects a build
  without BIP434 makes anyway, the pinned release having no `FEATURE` message
  (added with bitcoin/bitcoin@6a129983c9bf); the shape asserted is read from the
  build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
  The length and acceptance checks need `-peertimeout` and belong to
  [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14).
- `feature_uacomment.py`: a smaller claim: no `testnode{i}` default comment, no
  length or unsafe-character checks. Skips on `ua_comment`: `cli.py` registers
  no `-uacomment`
  ([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)).
- `rpc_uptime.py`: Core's claim in full. Skips on `clock`.
- `feature_torcontrol.py`:
  [ISS 23](https://github.com/btclib-org/bitcoin-node-tests/issues/23).
  `-torcontrol` drives a mock Tor control server the test carries. A smaller
  claim: the proof-of-work defenses step is asserted as the build under test
  takes it
  ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
- `p2p_compactblocks_blocksonly.py`: an option-family row
  ([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)). Skips on
  `blocks_only`: `cli.py` registers no `-blocksonly`. What a `-blocksonly` node
  does with a `cmpctblock` is read from the build
  ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)).
- `rpc_echo_payload.py`: skips on `rpc_work_queue`: `cli.py` registers neither
  `-rpcworkqueue` nor `-rpcthreads`
  ([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)). A
  smaller claim: the refusal is matched on its HTTP status alone.
- `rpc_getblockfilter.py`: Core's claim in full. Skips on `block_filter_index`:
  no `-blockfilterindex`, no `getblockfilter`.
- `rpc_getblockfrompeer.py`: a smaller claim in its literals alone. Skips on
  `block_from_peer`: no `getblockfrompeer`.
- `p2p_node_network_limited.py`: Core's claim in full
  ([ISS 185](https://github.com/btclib-org/bitcoin-node-tests/issues/185)).
  Skips on `suspend_network`, which is `setnetworkactive`
  ([ISS btclib-node#1392](https://github.com/btclib-org/btclib-node/issues/1392)).
- `feature_presegwit_node_upgrade.py`: every assertion of Core's file, the
  blocks built in Core's shape because a `MiniWallet` block reindexes to full
  height. Skips on `test_activation_height`. Its restarts name new `extra_args`
  ([ISS 51](https://github.com/btclib-org/bitcoin-node-tests/issues/51)).
- `rpc_validateaddress.py`: Core's claim in full, on the main chain
  ([ISS 153](https://github.com/btclib-org/bitcoin-node-tests/issues/153),
  [ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63)). Skips
  on `validate_address`.
- `rpc_getdescriptorinfo.py`: Core's claim without its `-disablewallet` option
  ([ISS 174](https://github.com/btclib-org/bitcoin-node-tests/issues/174)).
  Skips on `descriptor_info`.
- `feature_framework_miniwallet.py`: a smaller claim: the default address mode
  only, no padding or tagging test
  ([ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4)).
  `confirmed_only`
  ([ISS 69](https://github.com/btclib-org/bitcoin-node-tests/issues/69)) skips
  on `generate`. `fee_rate` and TRUC
  ([ISS 103](https://github.com/btclib-org/bitcoin-node-tests/issues/103)) skip
  on `datacarrier`. Until it is declared,
  [ISS btclib-node#1397](https://github.com/btclib-org/btclib-node/issues/1397),
  [ISS btclib-node#1398](https://github.com/btclib-org/btclib-node/issues/1398)
  and
  [ISS btclib-node#1399](https://github.com/btclib-org/btclib-node/issues/1399)
  are not reached.
- `mempool_resurrect.py`: `MiniWallet.resync` needs `gettxout`
  ([ISS btclib-node#1388](https://github.com/btclib-org/btclib-node/issues/1388)).
- `mempool_spend_coinbase.py`: a narrower claim: it mines to maturity and never
  calls `invalidateblock`. The immature spend is refused as in Core
  ([ISS btclib-node#1328](https://github.com/btclib-org/btclib-node/issues/1328)).
- `rpc_generate.py`: skips on `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404),
  [ISS btclib-node#1396](https://github.com/btclib-org/btclib-node/issues/1396)).
- `rpc_signrawtransactionwithkey.py`: skips on `sign_raw_transaction`
  ([ISS btclib-node#1400](https://github.com/btclib-org/btclib-node/issues/1400)).
- `rpc_scantxoutset.py`: skips on `scan_utxo_set`
  ([ISS btclib-node#1406](https://github.com/btclib-org/btclib-node/issues/1406)).
- `mining_template_verification.py`: skips on `block_proposal`
  ([ISS btclib-node#1427](https://github.com/btclib-org/btclib-node/issues/1427)),
  then asks for `package_acceptance`
  ([ISS btclib-node#1494](https://github.com/btclib-org/btclib-node/issues/1494)).
- `mempool_accept_wtxid.py`: a `Peer` stands in for Core's
  `P2PInterface`.
- `rpc_orphans.py`: Core's claim in full.
- `p2p_tx_privacy.py`: a `Peer` sends `version` and `wtxidrelay` by hand
  and holds back its `verack`.
- `mempool_package_rbf.py`: the mempool-ancestor body alone restarts with
  `-maxmempool`, and skips on `maxmempool` where the node does not declare
  it. The release refuses the replacement `submitpackage` makes, `main` takes it
  ([ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334)).
- `feature_dersig.py`: a smaller claim: kept are `getdeploymentinfo`'s
  transition, the version floor (`bad-version`) and the non-DER signature
  ([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)).
  Skips on `test_activation_height`: `cli.py` registers no
  `-testactivationheight`.
- `feature_cltv.py`: as `feature_dersig.py`, with the `OP_CHECKLOCKTIMEVERIFY`
  failure reasons
  ([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)). The
  mempool row also skips on `accept_non_standard`; the block row needs only
  `mine`
  ([ISS btclib-node#1362](https://github.com/btclib-org/btclib-node/issues/1362)).
- `feature_csv_activation.py`: BIP68, BIP112 and BIP113 at Core's configured
  height. No version-floor row: Core's `ContextualCheckBlockHeader` reads no
  `DEPLOYMENT_CSV`. Skips on `test_activation_height`.
- `feature_nulldummy.py`: every step of Core's file
  ([ISS 64](https://github.com/btclib-org/bitcoin-node-tests/issues/64)), the
  spends signed with btclib
  ([ISS 165](https://github.com/btclib-org/bitcoin-node-tests/issues/165)).
  Skips on `test_activation_height`.
- `feature_dirsymlinks.py`: Core's claim in full
  ([ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)). Asks for
  no capability: the fact is the operating system's symlink resolution.
- `feature_posix_fs_permissions.py`: a smaller claim: no `wallets_path` check,
  no node wallet being started
  ([ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)).
- `rpc_createmultisig.py`: a smaller claim: `test_sortedmulti_descriptors_bip67`
  is dropped, its vectors being a fixture this repository does not carry
  ([ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4)). The
  construction row needs `createmultisig`, which btclib-node's dispatch table
  does not name. A script past `OP_16`'s count is built by hand, btclib
  refusing it
  [ISS btclib-org/btclib#2348](https://github.com/btclib-org/btclib/issues/2348).
  The (spend) row skips on `sign_raw_transaction`
  ([ISS btclib-node#1400](https://github.com/btclib-org/btclib-node/issues/1400),
  [ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)).
- `p2p_invalid_block.py`: Core's whole run as a body per row, wire and log.
  Skips on `clock`.
- `p2p_timeouts.py`: Core's claim in full; a refused start under a non-positive
  `-peertimeout` has a row of its own. Skips on `peer_timeout`: `cli.py`
  registers no `-peertimeout`, and `setmocktime` names no callback
  ([ISS btclib-node#1479](https://github.com/btclib-org/btclib-node/issues/1479)).
- `p2p_ping.py`: Core's claim in full. Skips on `peer_timeout`, as
  `p2p_timeouts.py`.
- `mempool_expiry.py`: Core's claim in full. Skips on `mempool_expiry`: `cli.py`
  registers no `-mempoolexpiry`.
- `feature_includeconf.py`: a row per refusal of Core's file. The order row
  skips on `ua_comment`; the others run
  ([ISS btclib-node#1116](https://github.com/btclib-org/btclib-node/issues/1116),
  [ISS btclib-node#1409](https://github.com/btclib-org/btclib-node/issues/1409),
  [ISS btclib-node#1403](https://github.com/btclib-org/btclib-node/issues/1403),
  [ISS btclib-node#1187](https://github.com/btclib-org/btclib-node/issues/1187),
  [ISS btclib-node#1402](https://github.com/btclib-org/btclib-node/issues/1402)).
- `feature_reindex_init.py`: Core's claim in full. Skips on
  `reindex_after_failure`: `cli.py` registers no `-test`.
- `feature_reindex.py`: a row per step of Core's `run_test`. Skips on `reindex`
  ([ISS btclib-node#1415](https://github.com/btclib-org/btclib-node/issues/1415)).
- `feature_reindex_readonly.py`: Core's claim, with the file's mode alone and
  not the immutable flag. Skips on `reindex`
  ([ISS btclib-node#1415](https://github.com/btclib-org/btclib-node/issues/1415)).
- `p2p_message_capture.py`: Core's claim. Skips on `capture_messages`: `cli.py`
  registers no `-capturemessages`.
- `feature_blocksxor.py`: Core's claim, with the first block file asserted
  obfuscated. Skips on `blocks_xor`: `cli.py` registers no `-blocksxor`.
- `feature_remove_pruned_files_on_startup.py`: Core's claim. Skips on
  `fastprune`: `cli.py` registers no `-fastprune`.
- `feature_startupnotify.py`: Core's claim. Skips on `startup_notify`
  ([ISS btclib-node#1449](https://github.com/btclib-org/btclib-node/issues/1449)).
- `rpc_dumptxoutset.py`: every check of Core's file but the hashes it asserts as
  constants, asserted against the same node. Skips on `dump_utxo_set`
  ([ISS btclib-node#1471](https://github.com/btclib-org/btclib-node/issues/1471)).
- `feature_loadblock.py`: Core's claim, the test writing the block file itself
  in the format `linearize-data.py` writes. Skips on `load_block`, left out by
  decision
  ([ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)).
- `feature_port.py`: Core's claim; bitcoind's test runs on
  `UnboundBitcoindAdapter`, which leaves out its `-bind`. Skips on
  `debug_log`. Onion binds:
  ([ISS btclib-node#1644](https://github.com/btclib-org/btclib-node/issues/1644),
  [ISS btclib-node#1666](https://github.com/btclib-org/btclib-node/issues/1666)).
- `feature_maxtipage.py`: Core's claim, its blocks built client-side. Skips on
  `max_tip_age`
  ([ISS btclib-node#1474](https://github.com/btclib-org/btclib-node/issues/1474)).
- `p2p_blockfilters.py`: Core's claim in full. Skips on `peer_block_filters`
  ([ISS btclib-node#1395](https://github.com/btclib-org/btclib-node/issues/1395)).
- `p2p_getaddr_caching.py`: Core's claim, bitcoind's test running on
  `UnboundBitcoindAdapter`. Skips on `known_addresses`, and asks for
  `clock` besides
  ([ISS btclib-node#1443](https://github.com/btclib-org/btclib-node/issues/1443)).
- `mempool_reorg.py`: Core's claim in full. The (coinbase) row skips on
  `invalidate_block`
  ([ISS btclib-node#1480](https://github.com/btclib-org/btclib-node/issues/1480)),
  the (relay) row on `clock`
  ([ISS btclib-node#1479](https://github.com/btclib-org/btclib-node/issues/1479)).
- `interface_rpc.py`: the work queue step is read off the HTTP reply, not
  through `bitcoin-cli`
  ([ISS 49](https://github.com/btclib-org/bitcoin-node-tests/issues/49)).
  `getrpcinfo` skips on `rpc_info`
  ([ISS btclib-node#1486](https://github.com/btclib-org/btclib-node/issues/1486)),
  the work queue row on `rpc_work_queue`, the notification row on `generate`.
  The batch and status rows rest on requests being parsed as Core does
  ([ISS btclib-node#1109](https://github.com/btclib-org/btclib-node/issues/1109)).
- `p2p_ibd_txrelay.py`: Core's claim. Skips on `clock`
  ([ISS btclib-node#1479](https://github.com/btclib-org/btclib-node/issues/1479)).
  The top `feefilter` bucket follows `-minrelaytxfee`, not Core's default
  ([ISS btclib-node#1374](https://github.com/btclib-org/btclib-node/issues/1374)).
- `feature_bip68_sequence.py`: Core's claim in full. Skips on
  `test_activation_height`, then `invalidate_block`
  ([ISS btclib-node#1480](https://github.com/btclib-org/btclib-node/issues/1480)).
- `mempool_accept.py`: Core's claim in full. The release stops at a
  replacement it refuses
  ([ISS btclib-node#1334](https://github.com/btclib-org/btclib-node/issues/1334)),
  and `main` passes.
- `mempool_cluster.py`: Core's claim in full. Skips on `limit_cluster_size`
  ([ISS btclib-node#1383](https://github.com/btclib-org/btclib-node/issues/1383)),
  then asks for `mempool_graph`
  ([ISS btclib-node#1501](https://github.com/btclib-org/btclib-node/issues/1501)),
  `cluster_linearization`
  ([ISS btclib-node#1499](https://github.com/btclib-org/btclib-node/issues/1499))
  and `package_acceptance`
  ([ISS btclib-node#1494](https://github.com/btclib-org/btclib-node/issues/1494)).
- `feature_minchainwork.py`: Core's claim in full. Skips on `minimum_chain_work`
  ([ISS btclib-node#1500](https://github.com/btclib-org/btclib-node/issues/1500)).
  Core's `test_outbound_insufficient_work_disconnect` (bitcoin/bitcoin#36426) is
  the (outbound) row, which also asks for `mine`, `typed_outbound` and
  `debug_log`.
- `mempool_packages.py`: Core's claim in full. Skips on `mempool_graph`
  ([ISS btclib-node#1501](https://github.com/btclib-org/btclib-node/issues/1501));
  it needs `prioritisetransaction` too
  ([ISS btclib-node#1502](https://github.com/btclib-org/btclib-node/issues/1502)).
- `feature_versionbits_warning.py`: Core's claim. Skips on `alert_notify`
  ([ISS btclib-node#1475](https://github.com/btclib-org/btclib-node/issues/1475)).
- `p2p_headers_sync_with_minchainwork.py`: Core's claim in full. Skips on
  `minimum_chain_work`
  ([ISS btclib-node#1500](https://github.com/btclib-org/btclib-node/issues/1500)),
  then `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404)).
  The abort step reads stderr through `NodeAdapter.wait_until_stopped`
  ([ISS 318](https://github.com/btclib-org/bitcoin-node-tests/issues/318)).
- `p2p_unrequested_blocks.py`: Core's claim in full. Skips on
  `minimum_chain_work`
  ([ISS btclib-node#1500](https://github.com/btclib-org/btclib-node/issues/1500)),
  then `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404)).
- `p2p_1p1c_network.py`: Core's claim in full.
- `mempool_ephemeral_dust.py`: a row per subtest of Core's file. The package
  bodies skip on `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404)),
  and ask for `prioritisetransaction`
  ([ISS btclib-node#1502](https://github.com/btclib-org/btclib-node/issues/1502))
  and `-whitelist`
  ([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320))
  besides.
  The nonzero-dust body needs `-minrelaytxfee`
  ([ISS btclib-node#1332](https://github.com/btclib-org/btclib-node/issues/1332)).
  In the reorg body, a mined parent with a dust output and a fee returns to
  the mempool
  ([ISS btclib-node#1594](https://github.com/btclib-org/btclib-node/issues/1594)).
- `feature_notifications.py`: a row per option. Skips on `block_notify` and
  `shutdown_notify`
  ([ISS btclib-node#1519](https://github.com/btclib-org/btclib-node/issues/1519)),
  `alert_notify`
  ([ISS btclib-node#1475](https://github.com/btclib-org/btclib-node/issues/1475)).
  `-walletnotify` is not ported: it needs the node wallet (*The node wallet*
  below).
- `feature_settings.py`: Core's claim in full. Skips on `settings_file`
  ([ISS btclib-node#1523](https://github.com/btclib-org/btclib-node/issues/1523)).
- `feature_assumevalid.py`: Core's claim in full. Skips on `assume_valid`
  ([ISS btclib-node#1576](https://github.com/btclib-org/btclib-node/issues/1576)).
- `feature_rbf.py`: Core's claim in full. Skips on `incremental_relay_fee`
  ([ISS btclib-node#1596](https://github.com/btclib-org/btclib-node/issues/1596)).
- `p2p_permissions.py`: Core's claim in full. Skips on `peer_permissions`
  ([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320),
  [ISS btclib-node#1625](https://github.com/btclib-org/btclib-node/issues/1625)).
- `feature_shutdown.py`: has no row
  ([ISS 317](https://github.com/btclib-org/bitcoin-node-tests/issues/317)). Its
  subject is the exit of a node asked to `stop` over RPC, which
  `NodeAdapter.wait_until_stopped` reads
  ([ISS 318](https://github.com/btclib-org/bitcoin-node-tests/issues/318));
  `NodeAdapter.stop` sends `SIGTERM` and cannot tell them apart.
- `rpc_getchaintips.py`: Core's claim in full. Skips on `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404));
  it needs `submitheader` too
  ([ISS btclib-node#1533](https://github.com/btclib-org/btclib-node/issues/1533)).
- `rpc_preciousblock.py`: Core's claim in full. Skips on `precious_block`
  ([ISS btclib-node#1534](https://github.com/btclib-org/btclib-node/issues/1534)),
  then `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404)).
- `rpc_invalidateblock.py`: Core's claim in full. Skips on `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404));
  it needs `submitheader`
  ([ISS btclib-node#1533](https://github.com/btclib-org/btclib-node/issues/1533)),
  `invalidateblock`
  ([ISS btclib-node#1480](https://github.com/btclib-org/btclib-node/issues/1480))
  and `reconsiderblock`
  ([ISS btclib-node#1536](https://github.com/btclib-org/btclib-node/issues/1536)).
- `rpc_signmessagewithprivkey.py`: Core's claim in full. Skips on
  `sign_message_with_privkey`
  ([ISS btclib-node#1538](https://github.com/btclib-org/btclib-node/issues/1538)).
- `feature_chain_tiebreaks.py`: Core's claim in full. Skips on
  `invalidate_block`
  ([ISS btclib-node#1480](https://github.com/btclib-org/btclib-node/issues/1480));
  it needs `generatetoaddress`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404))
  and `submitheader`
  ([ISS btclib-node#1533](https://github.com/btclib-org/btclib-node/issues/1533)).
- `p2p_sendheaders.py`: Core's claim in full. Skips on `generate`
  ([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404));
  it needs `invalidateblock`
  ([ISS btclib-node#1480](https://github.com/btclib-org/btclib-node/issues/1480)).
- `p2p_fingerprint.py`: Core's claim in full. Skips on `clock`: `setmocktime` is
  named by no callback
  ([ISS btclib-node#1479](https://github.com/btclib-org/btclib-node/issues/1479)).
- `rpc_estimatefee.py`: Core's claim in full. Skips on `estimate_smart_fee`
  ([ISS btclib-node#1543](https://github.com/btclib-org/btclib-node/issues/1543)).

## Node-linking: `connect_nodes`, `disconnect_nodes` and the sync waits

[ISS 43](https://github.com/btclib-org/bitcoin-node-tests/issues/43):
`node.connect_nodes` and `node.wait_until_tips_agree` (Core's own
`sync_blocks`) already existed, from step 3's own adapter
(commit `4e64822`); this issue adds what step 3 did not need yet.
`node.wait_until_mempools_agree` is Core's own `sync_mempools`, and
`node.sync_all` is `wait_until_tips_agree` then `wait_until_mempools_agree`,
matching Core's own `sync_all`'s order and dropping only
`syncwithvalidationinterfacequeue`, a background-queue flush neither
adapter has an equivalent of. `node.wait_until_disconnected` is the wait
half of `disconnect_nodes` pulled out on its own, for a drop triggered
some other way than this suite's own `disconnectnode` call -- `setban`'s
own subject. Each is unit-tested against a fake RPC client, `node_test.py`'s
own style throughout.

`Capability.DISCONNECT` (`disconnectnode`) and `Capability.BAN`
(`setban`/`listbanned`/`clearbanned`) join `Capability.CONNECT` as
node-linking's own RPCs: `addnode`, `disconnectnode` and `setban` are
each their own, so a node answering one is not thereby assumed to
answer either of the others. Both are in bitcoind's own `help` listing
with no argument, unconditional the same way `CONNECT` already is.
`btclib-node` declares `DISCONNECT` only on a build serving
`disconnectnode`, `main` from `24de126d` on
([ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193)),
and `BAN` only on a build past
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088),
the `rpc_setban.py` paragraph below.

**A real finding, from building the mechanism rather than from reading about
it**: `connect_nodes`'s own `addnode ... "onetry"` left bitcoind's own
`v2transport` argument unset -- harmless between a pair of `BitcoindAdapter`s,
both defaulting the same way, but fatal the moment `first` is a
`BitcoindAdapter` dialling a `BtclibNodeAdapter`: bitcoind's own `debug.log`
read "start sending v2 handshake" immediately followed by "socket closed,
disconnecting", and the handshake wait timed out. No test built before this
issue ever dialled one kind of node from the other, so nothing had exercised
this path. bitcoind itself never falls back to v1 once a v2 attempt is reset by
the other side
([ISS btclib-node#1197](https://github.com/btclib-org/btclib-node/issues/1197)),
so `connect_nodes` now passes `v2transport` explicitly rather than leaning on a
fallback, matching Core's own `connect_nodes`'s `peer_advertises_v2` parameter,
here with a default of `False`, the one wire `Peer` speaks -- a `btclib-node`
build without `-v2transport` reads and type-checks the argument without acting
on it
([ISS btclib-node#1190](https://github.com/btclib-org/btclib-node/issues/1190)).
A test whose subject is BIP324 itself, `v2transport_option_test.py`, passes
`True`. Measured against the fix: the mixed-cluster test below, which timed out
before it and passes after, on every `btclib-node` build measured.

This suite runs `btclib-node` with `-v1transport` on wherever the build accepts
it (`BtclibNodeAdapter._command`, decided by a probe), because `Peer` speaks v1
only and btclib-node refuses v1 once `-v1transport` is off
([ISS btclib-node#1190](https://github.com/btclib-org/btclib-node/issues/1190)).
With v1 off the node drops every `Peer` at its first bytes and refuses `addnode`
and `addconnection` with `v2transport` off. A build without the flag gets none.

`rpc_setban.py` is ported, its own rows above. Core's own file restarts a node
repeatedly, some of those with different `extra_args` than it started with and
some with the same. The different-`extra_args` restarts -- the `-whitelist`
noban-permission section and the `-bantime` section -- are `NodeAdapter.restart`
(`node.py`) given its own `extra_args`, which it uses for that start alone, the
way Core's own `restart_node(i, extra_args)` does
([ISS bitcoin-node-tests#51](https://github.com/btclib-org/bitcoin-node-tests/issues/51)):
a banned peer connecting once the node is restarted with its address
whitelisted, `getpeerinfo` naming `noban` among its permissions while
`listbanned` still lists the ban; and a ban added after a restart with
`-bantime` given that duration. The same-`extra_args` restarts are `restart`
given none: a ban surviving a plain restart, checked against `listbanned` before
the refused reconnection is attempted at all
([ISS 94](https://github.com/btclib-org/bitcoin-node-tests/issues/94)). The
reconnection is then Core's own, an `addnode ... "onetry"` inside
`assert_debug_log`: bitcoind's own `CreateNodeFromAcceptedSocket`
(`src/net.cpp`) logs `dropped (banned)` as it refuses the accepted socket, and
the dialling node's `getpeerinfo` stands in for Core's wait on that node's own
log for the disconnect. Reconnection succeeds again once the ban is lifted. Kept
alongside them: a live connection dropping the moment `setban` matches its
address, `node.wait_until_disconnected` standing in for Core's own wait on
`is_connected_to` going false; and the non-IP address check, which needs no
second node at all. `btclib_node.py`'s own `_serves_ban_list` probe declares
`Capability.BAN` on a build past
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088)
([ISS 140](https://github.com/btclib-org/bitcoin-node-tests/issues/140)), so
each row is one body run against both nodes (`tests/integration/conftest.py`'s
own module docstring). The restart row skips on `Capability.DEBUG_LOG`; the ban,
`-bantime`, noban
([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320))
and non-IP
([ISS btclib-node#1218](https://github.com/btclib-org/btclib-node/issues/1218))
rows pass.

`p2p_disconnect_ban.py`'s "Test disconnectnode RPCs" section is ported, its own
row above: a pair of nodes connected both ways, `disconnectnode` refusing an
address and a node id given together and an address no peer has, then dropping a
peer by address, the pair reconnecting, and dropping a peer by node id. Both
measured `btclib-node` builds serve `disconnectnode`
([ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193)),
declare `Capability.DISCONNECT`, and pass. The file's `setban` half is not
ported: it reads `ban_duration` and `time_remaining` under `setmocktime`, waits
for "Recreating the banlist database" in `debug.log`, and deletes `banlist.json`
from the data directory -- the clock, log and disk families beside node-linking,
which makes it
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s.

A cluster mixing bitcoind and btclib-node -- the issue's own "most valuable
case" -- is `tests/integration/conftest.py`'s new `mixed_cluster` fixture: one
fresh node of each kind, started independently and left to a test's own
`connect_nodes` to wire together, matching `bitcoind_cluster`'s own shape.
`tests/integration/mixed_cluster_block_sync_btclib_node_test.py` exercises it:
bitcoind mines, and btclib-node -- never asked to mine anything itself --
receives the block over a real connection and its own tip converges. Not a
per-test ledger row: no Core file poses this question, Core's own tests running
one binary against copies of itself. **Passes on a `btclib-node` build past the
v2transport fix above**, which is what this needed, not `Capability.MINE`, which
only some `btclib-node` builds declare: nothing here asks the connecting side to
mine anything of its own.

Read at Core's `master` `ed7dd7cf4e`, every file
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags with multi-node p2p linkage, and every file this issue's own body
names, also carries `MiniWallet`, `setmocktime`, `assert_debug_log` or a
read of the node's own files -- one of step 5's other families beside
this one -- so none of them needs node-linking alone. Each is [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
where the census names no disqualifier of its own, and stays behind that
disqualifier where it does. What this issue ports is `rpc_setban.py`
and `p2p_disconnect_ban.py`'s `disconnectnode` half, the latter a
section needing node-linking alone. The files this issue's body names
go as follows.

- `interface_rest.py` (option, MiniWallet, disk) and
  `mining_getblocktemplate_longpoll.py` (log, MiniWallet): ISS 14's.
- `feature_fee_estimation.py` (MiniWallet, log, `-blockmaxweight`),
  `mining_basic.py` (MiniWallet, `setmocktime`, `-blockmaxweight`,
  `-prune`), `p2p_segwit.py` (MiniWallet, log, `-testactivationheight`)
  and `rpc_rawtransaction.py` (MiniWallet, `-txindex`, `-prune`):
  ISS 14's.
- `feature_bip68_sequence.py` (MiniWallet, `setmocktime`,
  `-testactivationheight`): ISS 14's, ported, its row in the table
  above.
- `rpc_txoutproof.py` (MiniWallet, `-txindex`): ISS 14's, and it also
  needs `sync_txindex`, Core's own wait for a `-txindex` to catch up,
  which is a different primitive from
  `wait_until_tips_agree`/`wait_until_mempools_agree` and is not built
  by this issue.
- `p2p_v2_transport.py` (`-v2transport`, log, a raw socket): ISS 14's,
  on bitcoind alone: it matches Core's own debug-log lines ("start sending
  v2 handshake", "retrying with v1 transport protocol", "V2 transport
  error: ..."), so it needs `Capability.DEBUG_LOG`, which
  `BtclibNodeAdapter` does not declare.
- `p2p_blockfilters.py` (`-blockfilterindex`, `-peerblockfilters`, log,
  and BIP157's own `getcfilters`/`getcfheaders`/`getcfcheckpt` from a
  raw peer): ISS 14's, ported, its row in the table above.
- `mempool_reorg.py` (MiniWallet, `setmocktime`, `-whitelist`): ISS 14's,
  ported, its rows in the table above.
- `p2p_disconnect_ban.py`'s `setban` half: ISS 14's, the paragraph
  above.
- `feature_assumeutxo.py` stays disqualified on the sixth thing the
  census already named: a background IBD racing a live feed, which no
  mechanism here builds.

`mempool_datacarrier.py`, `mempool_dust.py` and `mempool_sigoplimit.py`
are ISS 14's own mempool-policy-option trio, each combining a
relay-policy option with MiniWallet the same way the softfork-activation
trio above combines one with `Capability.MINE`. Each needed a helper
`mini_wallet.py` did not yet carry: `nulldata_script_pub_key`, an
`OP_RETURN` scriptPubKey of any length (`ScriptPubKey.nulldata`'s own
byte-length refusal is the historical "standard" bound, which a
`-datacarriersize` test asks a node about rather than a fact this
library should enforce before the request is ever sent), and
`MiniWallet.send_to` (Core's own `wallet.py`), paying a second output
while keeping a fixed-fee change output cached back to the wallet once
the node accepts the transaction. Both are unit-tested
against the fake RPC alongside the rest of `mini_wallet_test.py`.

`mempool_datacarrier.py`'s own row is a smaller claim than Core's own
file: kept is that the default setting relays a sizeable `OP_RETURN`,
`-datacarrier` disabled refuses one of any size (even a bare, empty
one), a custom `-datacarriersize` bounds the payload at its own
boundary, and bare multisig is permitted by default, the check Core's own file
carries for `mempool_dust.py`'s option. Dropped is Core's own extra node, a
further custom `-datacarriersize` value, and its own sweep of
`None`/empty/single-byte payloads across every node, neither reaching a
boundary the kept configurations do not already cover.

Both bitcoin/bitcoin#29954 and bitcoin/bitcoin#32406 are first in `v30.0rc1`.
`getmempoolinfo` says bare multisig is permitted where the build reports
`permitbaremultisig` (bitcoin/bitcoin#29954); without it,
`testmempoolaccept` allows a bare multisig output. Without
bitcoin/bitcoin#32406 a null-data output is capped at the older
`-datacarriersize` default, so the default check asserts a payload at that cap
relays and one byte more is refused, and every refusal reads `scriptpubkey`,
not `datacarrier`.

`mempool_dust.py`'s own row is a smaller claim than Core's own file too: kept is
that a value clearly under the dust threshold is refused and one clearly over it
is allowed, for every output shape Core's own list names that `ScriptPubKey`
builds -- P2PK uncompressed and compressed, P2PKH, P2SH, P2WPKH, P2WSH, P2TR and
the largest standard bare multisig -- and that `-dustrelayfee` disabled waives
the check entirely. Dropped is Core's own file's exact per-byte threshold
arithmetic (`GetDustThreshold`'s own formula), its future-witness-version rows,
`ScriptPubKey` having no generic future-witness-version output of its own, its
null data row, whose threshold is zero and so sits on neither side of a
boundary, its own sweep of several other `-dustrelayfee` values, and its own
ephemeral-dust scenario. Ephemeral dust is not the dust threshold at a coarser
grain but its own acceptance rule, `src/policy/ephemeral_policy.cpp`'s
`CheckEphemeralSpends`, exempting a dust output its package spends. It is the
subject of Core's own `mempool_ephemeral_dust.py`, which has rows of its own.

`mempool_sigoplimit.py`'s own row is a smaller claim than Core's own
file: kept is `testmempoolaccept`'s own `vsize` floor, `max` of the
sigop-equivalent size and the serialized one, at that boundary, a byte
above it and a byte below it, for a witness script built directly
(`OP_FALSE OP_IF <OP_CHECKSIG ...> OP_ENDIF OP_TRUE`: the branch
carrying the sigops is never executed, legacy sigop counting being
syntactic rather than a trace of execution, so no signature is ever
needed), at one `-bytespersigop` and sigop count rather than Core's own
sweep across both. Dropped is Core's own file's ancestor and descendant
size accounting (`getmempoolentry`), its package-limit scenario
(`submitpackage`, cluster limits) and its legacy P2SH sigops
standardness test, all driving package or standardness mechanics beyond
a single transaction's own accepted vsize. Measured live against the
pinned release: `testmempoolaccept`'s own answer carries no
`vsize_adjusted` or `vsize_bip141` field there, `vsize` alone already
reflecting the sigop-adjusted floor. Its node restarts with a
`-datacarriersize` besides (`Capability.DATACARRIER`), over the
`OP_RETURN` padding of the transactions it builds, which a build without
bitcoin/bitcoin#32406, first in `v30.0rc1`, refuses by default.

`BtclibNodeAdapter` declares `PERMIT_BARE_MULTISIG` on a build past
[ISS btclib-node#1497](https://github.com/btclib-org/btclib-node/issues/1497),
and none of `DATACARRIER`, `DUST_RELAY_FEE` or `BYTES_PER_SIGOP`. A body asking
for one it does not declare is a counted skip ahead of `Capability.MINE`.
`mempool_dust.py`'s refusal body fails on a build before the fix
[ISS btclib-node#1594](https://github.com/btclib-org/btclib-node/issues/1594)
asks for and does not fail on one past it.

`mempool_package_limits.py`'s row is a smaller claim than Core's own
file: kept is one ancestor-side case (a chain of in-mempool ancestors, a
package extending it, both counted together against
`-limitclustercount`) and one descendant-side case (a top parent with
several chains hanging off it at differing depths, its own descendants
only exceeding the limit once a package extending every chain joins
them). Dropped is Core's own file's further splits of the ancestor case
and its own second descendant shape (`test_desc_count_limits_2`) --
each a different split of a mechanism the kept case already
demonstrates -- and its own descendant-size case
(`test_desc_size_limits`), which needs `target_vsize` at a size large
enough to make a real functional-test run slow, disproportionate for a
size boundary neither kept case needs to also cover. `mini_wallet.py`
gains `create_self_transfer_multi` and `create_self_transfer_chain`
(Core's own methods of the same names, `fee_per_output` in satoshis as
in Core) and a `target_vsize` on every `create_self_transfer*` method,
an `OP_RETURN` of literal `OP_1`
opcodes padding a transaction to an exact size the way Core's own
`bulk_vout` does; `get_utxo` gains a `vout` alongside `txid`,
disambiguating several cached coins a multi-output send caches under
one txid. Every addition is unit-tested against the fake RPC alongside
the rest of `mini_wallet_test.py`.

`mempool_updatefromblock.py`'s row is a smaller claim than Core's own
file too: kept is the acyclic-tournament mechanism -- every mempool
entry's own ancestor/descendant count and size recomputed once a reorg
re-adds every transaction a mined block once carried -- at a
`_TOURNAMENT_SIZE` far smaller than Core's own `DEFAULT_CLUSTER_LIMIT`,
the mechanism needing no particular size to hold, and the chain-length
case, unchanged: it is bitcoind's own *default* cluster count the chain
has to exceed, not `-limitclustersize`, this file's only configured
option. Dropped is Core's own `test_max_disconnect_pool_bytes`:
`MAX_DISCONNECTED_TX_POOL_BYTES` is a large fixed bound in bitcoind's
own C++ rather than a configurable option, so exercising it means
building, mining and reorging a disproportionate volume of transactions
for a boundary neither kept case needs to also cover.

Where a build has no cluster mempool, `mempool_updatefromblock.py` runs its
tournament unchanged and its chain at the default ancestor limit, refused
`too-long-mempool-chain`. `mempool_package_limits.py` is a counted skip on
`Capability.LIMIT_CLUSTER_COUNT`, Core's file starting its node under
`-limitclustercount` and asserting `too-large-cluster` alone.

`mempool_package_limits.py`'s `btclib-node` cells are a counted skip on
`Capability.LIMIT_CLUSTER_COUNT`, ahead of `Capability.PACKAGE_ACCEPTANCE` and
`Capability.MINE`.
`mempool_updatefromblock.py`'s chain-length case is a counted skip on
`Capability.GENERATE`, for its own `generateblock`, ahead of
`Capability.MINE`. Its tournament asks for `Capability.MINE` alone, and
passes on the released `btclib-node` and on its `main`:
`getmempoolentry` (`get_mempool_entry` in `rpc/callbacks.py`) answers the
ancestor and descendant counts and sizes it reads. On either build
the row's cell is the chain case's skip.

`p2p_leak_tx.py`'s own rows are the clock and MiniWallet families
together, each subject its own pytest function over `Peer` and
`NodeAdapter` rather than Core's own
`P2PInterface`/`P2PDataStore`/`P2PTxInvStore`. "in block" is Core's own
`test_tx_in_block`: a `getdata` built from the `inv` the node announces,
sent only after the transaction has been mined into a block, is still
answered with the transaction. Its `getpeerinfo` checks are read per-build:
`last_inv_sequence` and `inv_to_send` are in the node's answer only on a
build carrying bitcoin/bitcoin#33448, which `v31.0rc1` is the first tag to
carry, so the body reads the build's own `help getpeerinfo` and leaves those
checks out on an older build. Each connection is synced with a ping after its
handshake, as Core's `TestNode.add_p2p_connection` does, so the node has
processed this peer's own `verack` before any transaction is broadcast or the
mock clock moves. Each subject starts its own node rather than sharing one
across the module: `mempool_sequence` is a counter over a node's whole lifetime,
and `pytest-randomly` does not hold that ordering against a shared node still.
The `btclib-node` cells skip on `Capability.CLOCK`, the first capability each
subject asks for on either node.

`feature_utxo_set_hash.py`'s row computes the UTXO set's own commitments
independently, walking every block this harness's own chain holds back off
`getblock`, rather than trusting Core's own Python reimplementation of the same
arithmetic the way Core's own file does: MuHash with
`btclib.coinstats.CoinStats`, and `hash_serialized_3` as the SHA256d Core's
`kernel/coinstats.cpp` takes over the same `TxOutSer` bytes, in its coins-view
cursor's own order. Kept is that both agree with `gettxoutsetinfo` over a chain
carrying a coinbase-only run and one spend; dropped is Core's own hard-coded
`hash_serialized_3`/`muhash` literals, deterministic only on Core's own exact
chain. The row is one body run against both nodes. A build whose bare
`gettxoutsetinfo` answers no `hash_serialized_3`, Core's own default
`hash_type`, fails it, its MuHash agreeing; a build past
[ISS btclib-node#1598](https://github.com/btclib-org/btclib-node/issues/1598)
passes.

Neither `feature_utxo_set_hash.py` nor `rpc_getdescriptoractivity.py`
nor `rpc_getblockstats.py` is the clock family, despite Core's own file
calling `setmocktime` in each. In `feature_utxo_set_hash.py` and
`rpc_getdescriptoractivity.py` that call freezes the clock Core's own
node-driven mining (`generatetodescriptor`) reads block times from,
where this harness's own `MiniWallet.generate` always builds a block's
own time from the wall clock instead -- freezing the node's clock ahead
of a `generate` call produces a `time-too-new` refusal rather than the
freeze Core's own file relies on, measured live on the first block mined
after the freeze. In `rpc_getblockstats.py` an ordinary run calls it
only in `load_test_data`, so that a node replaying its fixture's old
blocks leaves Initial Block Download; this port mines fresh blocks
rather than replaying that fixture, so nothing in it waits on the
freeze.

`rpc_getdescriptoractivity.py`'s own rows and `rpc_getblockstats.py`'s own row
are new capabilities rather than options: `Capability.DESCRIPTOR_ACTIVITY` and
`Capability.BLOCK_STATS` (`capability.py`) name the RPC itself,
`getdescriptoractivity` and `getblockstats` naming no callback in
`btclib-node`'s own dispatch table -- measured live, a build without them
answers "Method not found". The `rpc_getblockstats.py` cell abbreviates its
capability to `(stats)` and the `rpc_getdescriptoractivity.py` cells name none,
so this paragraph is where both names are spelled out.
`rpc_getdescriptoractivity.py`'s own first row needs no `MiniWallet`, and is
what runs on bitcoind directly; its `(mempool)` row folds together every one of
Core's own subtests that needs `Capability.MINE` on top of the RPC itself.
`rpc_getdescriptoractivity.py` drops none of Core's own subtests: kept is that
an unused address carries no activity; that a payment to a key-path p2tr output
confirmed in a named block makes `activity` the answer's only key and reports
one `receive` entry, checked for its `type`, `blockhash`, `height`, `txid`,
`vout` and `amount` and for its `output_spk`'s `hex`, `address`, `type`, the
witness version opening its `asm` and the `rawtr` function opening its `desc`;
that an unconfirmed payment is excluded when `include_mempool` is `False`; its
RPC-argument errors for a bad blockhash, a bad descriptor and a missing
argument; and Core's own multiple-address query, its mix of a confirmed and an
unconfirmed payment, its receive-then-spend, and its no-address case, a coin
paying `mini_wallet.py`'s `RAW_P2PK_SCRIPT_PUB_KEY` spent under
`raw_p2pk_script_sig`
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)).
`rpc_getblockstats.py`'s own kept and dropped set: kept is the genesis block's
own statistics -- independently computed as its serialized `TxOut` plus
`getblockstats`'s own per-coin overhead, the one the running build's
`getnetworkinfo` `version` implies, rather than copied from Core's own literals,
genesis being a network constant this harness's own chain shares with Core's --
and the same answer when the block is selected by hash; that an `OP_RETURN`
output is counted in `utxo_increase`/`utxo_size_inc` but excluded from
`utxo_increase_actual`/`utxo_size_inc_actual`; that `stats=[...]` narrows the
answer; its height error messages; its statistic-name error message wherever the
invalid name sits in the list, and naming the name given rather than a fixed
one; mainnet's genesis hash answering "Block not found"; its required-argument
usage string; and a `blk00000.dat` renamed away answering "Block not found on
disk". Dropped is Core's own vendored fixture and every comparison it feeds --
the full key set, the heights and each statistic of the blocks it replays, by
height and by hash -- its per-stat query loop over those blocks, and its
`submitheader`-only-known-block case.

`feature_fastprune.py`'s row is Core's own claim in full, reached
another way: a node under `-fastprune`, whose block files are far
smaller than a real node's, stores and connects a block larger than
one of them rather than crashing or freezing on it. Core pads a
`MiniWallet` transaction's witness with a BIP341 annex past a block
file's own size and mines it with `generateblock`, paying a raw script;
this pads it the same way and mines it client-side over `submitblock`,
`MiniWallet.generate`'s own `confirm` naming it, paying the wallet's
own script. Core asserts the block count its cached chain reaches; this
asserts the count its own fresh chain reaches, and that the new tip
carries the transaction and is larger than the annex.

`rpc_scanblocks.py`'s rows are Core's own claim in full: a scan by
address and by ranged `pkh()` descriptor, `start_height` and
`stop_height` bounding it, `filter_false_positives` either way, Core's
precomputed false positive colliding with the regtest genesis block's
coinbase output, every argument error Core's file asserts, and, on a
row of its own, a node started without `-blockfilterindex` refusing a
scan. That node is Core's second, independent of the first and asked
for nothing but the refusal, so it is its own test here. Core's
`generate` flushes the validation queue before returning; this waits
instead for `getindexinfo`'s own `best_block_height` to reach the tip,
`synced` staying true while the index is still behind a block just
mined. Core checks its false positive with
`bip158_basic_element_hash`; this builds the genesis block's own filter
with btclib's `BasicBlockFilter.from_block` and asks it to `match` both
scripts. Core's refusal of a null `scanobjects` is `master`'s wording
from the pinned commit on, and the pinned release refuses the same call
as a type error instead: either refusal passes, each with its own code.

`p2p_eviction.py`'s row is Core's own claim in full: inbound peers fill
the slots `-maxconnections` leaves for transaction-relaying peers, the
next one to connect triggers an eviction, exactly one peer is
disconnected, and it is none of those protected for sending a novel
block, for sending a transaction or for the lowest ping. How many
inbound slots a given `-maxconnections` leaves for such peers differs
between builds: the pinned commit lets transaction-relaying peers take
only a share of a node's inbound slots, and the pinned release does not
set them apart. So the value is read from the node's own `-help`
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)),
which names the share where the build has one -- in
`-maxconnections`'s own description at the pinned commit, as
`-inboundrelaypercent` on Core's `master` since -- and the test restarts
the node with Core's own value for the build it finds: the pinned
commit's, or the one Core's own file carried before it. `Peer` answers
a ping only while a caller reads, where Core's own peers answer from a
background thread, so the test reads for it: after each handshake it
answers the node's first ping, at once for a fast peer and after Core's
own delay for a slow one, and waits for the `sync_with_ping` barrier
Core's `add_p2p_connection` runs. Core sends a transaction without
waiting for it; this waits until the node's `getrawmempool` lists it
before the next peer connects, which that barrier would not ensure of a
node answering a `ping` ahead of the `tx` its peer sent first
([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410)).

Neither `-fastprune` nor `-blockfilterindex` is one of `cli.py`'s registered
flags, and `scanblocks` is not answered, so the cells asking for them are
counted skips. `Capability.INBOUND_EVICTION` is declared per instance, by
`btclib_node.py`'s own `_evicts_inbound` probe, and a build past
[ISS btclib-node#1064](https://github.com/btclib-org/btclib-node/issues/1064)
declares it, so `p2p_eviction.py`'s row then asks for `Capability.MINE`. There
the row is one body run against both nodes (`tests/integration/conftest.py`'s
own module docstring), and it passes on a build past
[ISS btclib-node#1179](https://github.com/btclib-org/btclib-node/issues/1179).

`tool_utxo_to_sqlite.py`, the last of this batch, is not ported. Its
subject is `contrib/utxo-tools/utxo_to_sqlite.py`, a script of Core's
own source tree the test finds through the build's own `config.ini`,
run against a UTXO set the node dumps: not a node, and not a file
`btclib-org/.github`'s `install_bitcoind.py` extracts from the release,
which is `bin/bitcoind` alone. What it asks of the node, `dumptxoutset`
and `gettxoutsetinfo`'s own MuHash, is the subject of Core's
`rpc_dumptxoutset.py` and `feature_utxo_set_hash.py`.

## Outbound connections: `Listener` and `addconnection`

[ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44):
a test listens and the node dials it, as Core's
`TestNode.add_outbound_p2p_connection` has it do. `peer.Listener` is
the listening side, bound to loopback before the node is asked to dial;
its backlog holds the node's connection until `accept` hands it over as
a `Peer` whose `handshake` answers the node's own `version`, the order
Core's `P2PInterface.on_version` follows on a connection the test did
not open. `NodeAdapter.add_outbound_connection` (`node.py`) is Core's
`addconnection`, `v2transport` off because `Peer` speaks v1 alone, and
`Capability.TYPED_OUTBOUND` is what a test asks for before calling it.
`Peer.message_count` is Core's own `message_count`, the tally a port
reads what the node sent from. `peer_test.py` drives the listener
against a fake dialling node, `node_test.py` the RPC against a fake
client.

bitcoind declares `TYPED_OUTBOUND` on regtest alone, `addconnection` refusing
any other chain (`src/rpc/net.cpp`). `btclib-node` declares it on no build,
though its dispatch table names `addconnection`.

`p2p_addrfetch.py` is the first file ported on it, its row above, every
assertion of Core's own kept. Its halves are separate bodies in
`tests/integration/p2p_addrfetch_test.py`, each over a fresh node, so
the second peer's node id is the first one a node gives rather than the
next, and each disconnect is awaited over `Peer`'s default wait rather
than Core's shorter one. `btclib-node`'s cell is a counted skip on
`TYPED_OUTBOUND`.

`p2p_add_connections.py` is ported on it too, every assertion of Core's
own kept, in `tests/integration/p2p_add_connections_test.py`.
Its first step, a `manual` connection once a full-relay one has filled a
node's outbound capacity (`-maxconnections` at one), is its own row, read
per-build
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)):
`addconnection` takes `manual` only past the pinned release
(bitcoin/bitcoin@4c79f3a34d003bd97824b032383ac816a4147d68), so the body
reads the build's own `help addconnection`, and where that names no
`manual` it asserts the refusal Core's `RPC_INVALID_PARAMETER` answers
instead. Its module docstring has what else differs from Core's file.

The rest of `p2p_handshake.py` is ported beside its redundant-`verack`
rows, each check a wire half and a log half over a fresh node, the log
family's own split: a peer short of the services an outbound type expects
is dropped and one offering them kept; a `NODE_NETWORK_LIMITED` peer is
dropped while the tip is more than a day old and kept once it is not; a
feeler is dropped once the node reads its `version`; and a node made to
dial its own address drops the connection. The limited rows mine at a
mock time, so they ask `MINE` and `CLOCK` besides, and flush bitcoind's
validation queue after each block as Core's own `generate` does.

`btclib-node`'s cell on every row of `p2p_add_connections.py` and
`p2p_handshake.py` but the redundant-`verack` ones is a counted skip on
`TYPED_OUTBOUND`.

`p2p_initial_headers_sync.py` is ported on it, each check a body over a
fresh node in `tests/integration/p2p_initial_headers_sync_test.py`. Its
first check, one peer asked for headers and one more per block announced,
dials the node alone and asks for no capability. Its timeout checks have
the node dial an outbound peer and move the clock past the headers
timeout, each a wire half and a log half, so they ask for `TYPED_OUTBOUND`,
`CLOCK` and `PEER_TIMEOUT`: the node restarts with settings Core's own
harness gives every node, a `-peertimeout` under which the moved clock
drops no peer as inactive, and automatic connections off. The `noban` check's
`-whitelist` asks for no capability, as `rpc_setban.py`'s own `noban` row
does not, so a `btclib-node` build declaring the rest would meet
[ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)
there.

`p2p_sendtxrcncl.py` is ported on it too, in
`tests/integration/p2p_sendtxrcncl_test.py`, Core's steps grouped into
bodies by the options Core restarts its node with, and a peer kept or
dropped given a wire half and a log half. `-txreconciliation` is
`Capability.TX_RECONCILIATION` and `-peerbloomfilters`
`Capability.PEER_BLOOM_FILTERS`. Where `-txreconciliation` is set, the node
restarts with the `-peertimeout` Core's harness gives every node too, under
`Capability.PEER_TIMEOUT`, so that a peer never sending `verack` is dropped
for its `sendtxrcncl` rather than by the handshake timeout. The steps
without `-txreconciliation` ask for none of these. The first body's
check at BIP339's lowest version passes on every `bitcoind` build
measured, so each cell is one verdict. bitcoind starts with
`-debug=txreconciliation` besides, the category the registered and forgotten
peers' lines are written under.

`btclib-node`'s cell on the first `p2p_initial_headers_sync.py` row is a pass on
a build past
[ISS btclib-node#1073](https://github.com/btclib-org/btclib-node/issues/1073).
On `p2p_sendtxrcncl.py` (off) it passes, and every other row these files add is
a counted skip.

`p2p_feefilter.py` is ported on it too, each of Core's checks a body over fresh
nodes in `tests/integration/p2p_feefilter_test.py`, whose module docstring has
what differs from Core's file. Its block-relay-only check asks for
`TYPED_OUTBOUND` and its `-blocksonly` check for `BLOCKS_ONLY`. Its filtering
check funds its transactions from a `MiniWallet` on a second node, relayed to
the node under test, so it asks for `MINE` of both nodes and `CONNECT` of the
second. The `forcerelay` check's `-whitelist` asks for no capability, as the
`noban` checks' do not, so a `btclib-node` build past
[ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320),
which registers `-whitelist`, passes it. `btclib-node`'s other cells are a pass
on `p2p_feefilter.py`'s own row and on the filtering row, and a counted skip on
the block-relay-only and `-blocksonly` rows.

`p2p_mutated_blocks.py` is ported on it too, each of Core's checks a wire half
and a log half over a fresh node in
`tests/integration/p2p_mutated_blocks_test.py`, whose module docstring has what
differs from Core's file. The mutated-block check has the node dial an outbound
full-relay peer, so it asks for `TYPED_OUTBOUND`, and `MINE` for the block it
announces, which spends a `MiniWallet` coin; the missing-parent check's wire
half asks for `MINE` alone. Each log half asks for `DEBUG_LOG` besides, and the
missing-parent one for `TEST_ACTIVATION_HEIGHT` too. Its pin is past the pinned
release: Core's file there sends a `sendcmpct` and the block's header ahead of
the `cmpctblock`, where the release's own sends neither, and each `bitcoind`
cell is one verdict for both builds. `btclib-node`'s cell on the missing-parent
wire row is a pass, and every other row this file adds is a counted skip.

`feature_anchors.py` is ported on it too, each of Core's checks a body
over a fresh node in `tests/integration/feature_anchors_test.py`,
whose module docstring has what differs from Core's file. Its first check
has the node dial block-relay-only peers beside inbound ones, and reads
`anchors.dat` once the node stops; its second has the node dial a Tor v3
address through a `Socks5Proxy` given as `-onion`, so it asks for `PROXY`
besides. Each asks for `TYPED_OUTBOUND` and `DEBUG_LOG`, Core's own log
lines being where the node's read of the file, and in the second its
dump, are asserted. `btclib-node`'s cell on each is a counted skip on
`TYPED_OUTBOUND`. The steps bitcoin/bitcoin#34213 added ask for
`SUSPEND_NETWORK`, and the onion body's for `ADDRESS_FETCH` and `CLOCK`
too. No release carries the change, so they run only on a build new enough
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)); the
module's own docstring has the steps, the version and its limit.

`p2p_addr_selfannouncement.py` is ported on it too, in
`tests/integration/p2p_addr_selfannouncement_test.py`, whose module
docstring has what differs from Core's file. Its self-announcement check
is a wire half and a log half to an inbound peer and to an outbound one,
each over a fresh node and run over `addr` and then over `addrv2`.
`Peer.handshake`'s `addrv2` sends the `sendaddrv2` Core's
`P2PInterface(support_addrv2=True)` does. Every such half asks for
`EXTERNAL_IP` for `-externalip`, `KNOWN_ADDRESSES` for the addresses a
`getaddr` is answered from, `MINE` to leave initial block download, and
`CLOCK` and `PEER_TIMEOUT` for Core's own mock time under its harness's
`-peertimeout`; the outbound halves ask for `TYPED_OUTBOUND` and each log
half for `DEBUG_LOG` besides. Its `-onlynet` check asks for `EXTERNAL_IP`
and `ONLYNET`, and its pin is past the pinned release, whose own file has
no such check: `-externalip` bypasses `-onlynet` only on a build carrying
bitcoin/bitcoin@8c87e32bd3937251d6f30295cc1924048e5b74d1, which the release
does not, so the body reads the build's own `getnetworkinfo` `version` and
asserts, on an older build, that the onion address is left out. Its inbound
checks are read per-build: the first self-announcement is alone in its
message only on a build carrying bitcoin/bitcoin#34146, first released in
`v31.0rc1`, so the body reads the build's own `getnetworkinfo` `version` and
asserts, on an older build, one message holding it and the `getaddr` answer.
`btclib-node`'s cell on each row is a counted skip.

`p2p_ibd_stalling.py` is ported on it too, each of Core's checks a wire
half and a log half over a fresh node in
`tests/integration/p2p_ibd_stalling_test.py`, whose module docstring has
what differs from Core's file. Each body asks for `TYPED_OUTBOUND`, and
`CLOCK` for Core's own mock time; each log half asks for `DEBUG_LOG`
besides. Its `manual` check is read per-build, as
`p2p_add_connections.py`'s is: where the build's own `help addconnection`
names no `manual`, it asserts the refusal instead. The (log) row is read
per-build too: a build without bitcoin/bitcoin#32180, which `v31.0rc1` is
the first tag to carry, logs `Stall started` once the block withheld first
is sent, so the body reads the build's own `getnetworkinfo` `version` and,
there, does not assert it absent
([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)).
`btclib-node`'s cell on each row is a counted skip.

`p2p_tx_download.py` is ported on it too, each of Core's checks a body
over a fresh node in `tests/integration/p2p_tx_download_test.py`, whose
module docstring has what differs from Core's file. Every body asks for
`MINE`, to leave initial block download, and every body moving Core's own
mock time for `CLOCK`; the tiebreak and outbound checks ask for
`TYPED_OUTBOUND`, the inv-block check for `CONNECT`, the rejection check
for `MAXMEMPOOL` and `DATACARRIER` and the duplicate check for `DEBUG_LOG`
besides. A peer
announcing by txid is `Peer.handshake`'s `wtxidrelay` off, Core's
`P2PInterface(wtxidrelay=False)`. Its `-whitelist` asks for no
capability, as the `noban` checks above do not.
The duplicate check is read per-build: the entries of one `inv` naming
the same transaction are processed once only on a build carrying
bitcoin/bitcoin@1278a5970d5ada0979052a5bad899e896b8ab40b, which the
pinned release does not, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, that each is
processed.
The inv-block check is read per-build too: `getpeerinfo`'s `inv_to_send`
is in the node's answer only on a build carrying bitcoin/bitcoin#33448,
which `v31.0rc1` is the first tag to carry, so the body reads the build's own
`help getpeerinfo` and leaves `inv_to_send` unread on an older build.

`btclib-node`'s cell on the spurious-`notfound`, disconnect, `notfound` and
large-inv rows is a pass on a build past
[ISS btclib-node#1196](https://github.com/btclib-org/btclib-node/issues/1196)
and
[ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320);
every other row this file adds is a counted skip.

`p2p_blocksonly.py` is ported on it too, each of Core's checks a wire
half and a log half over a fresh node in
`tests/integration/p2p_blocksonly_test.py`, whose module docstring has
what differs from Core's file. Every body asks for `MINE`, for the coin
its transaction spends; the `-blocksonly` check asks for `BLOCKS_ONLY`,
and the block-relay-only check for `TYPED_OUTBOUND`, and `CLOCK` for
Core's own mock time; each log half asks for `DEBUG_LOG` besides. Its
`-whitelist` asks for no capability, as the `noban` checks above do not.
`btclib-node`'s cell on each row is a counted skip, the `-blocksonly` rows'
on `BLOCKS_ONLY` and the block-relay-only rows' on `TYPED_OUTBOUND`.

`p2p_orphan_handling.py` is ported on it, its rows above each
one of Core's checks as a body over a fresh node in
`tests/integration/p2p_orphan_handling_test.py`, whose module docstring
has what differs from Core's file. Every body asks for `ORPHANAGE` first,
and for `CLOCK` and `MINE`; the prefer-outbound and announcers checks ask
for `TYPED_OUTBOUND`, the multiple-parents check for `INVALIDATE_BLOCK`,
the same-txid check for `DEBUG_LOG` besides, reading a line bitcoind
writes under the `-debug=mempoolrej` it starts with, and the
maximal-package check for `DATACARRIER`. That check restarts its node with
a `-datacarriersize` over the `OP_RETURN` padding of the package's last
transaction: a build without bitcoin/bitcoin#32406, which `v30.0rc1` is
the first tag to carry, refuses that padding by default. On a build
without bitcoin/bitcoin#31829, which `v30.0rc1` is the first tag to
carry, the orphanage evicts by count alone and the large orphans stay
under it, so the check asserts there only that the package is kept and
taken in. The parent-confirmed check is read per-build: an orphan is taken
into the mempool once a block confirms its parent only on a build
carrying bitcoin/bitcoin@9cc7dc50bdc9867d079ab7a111d39487a4566767, which
the pinned release does not, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, that the
orphan is kept. A transaction with no witness spends
`mini_wallet.py`'s `RAW_P2PK_SCRIPT_PUB_KEY`, Core's own `RAW_P2PK`
output, under `raw_p2pk_script_sig`, from coinbases the body mines.
`btclib-node`'s cell on each row is a counted skip, on `ORPHANAGE` or on a
later capability above.

`p2p_compactblocks.py` is ported on it, its rows above each one of
Core's checks, or the wire or the log half of one, as a body over a
fresh node in `tests/integration/p2p_compactblocks_test.py`, whose
module docstring has what differs from Core's file. Every body but the
invalid-`sendcmpct` and empty-`getblocktxn` ones asks for `MINE`, and
every log half for `DEBUG_LOG` besides, reading lines bitcoind writes
under the `-debug=net` it starts with. The outbound-`sendcmpct` and
parallel-reconstruction bodies have the node dial an outbound
full-relay peer, so they ask for `TYPED_OUTBOUND` ahead of `MINE`.
BIP152's messages are `btclib.p2p.compact_blocks`' own. Each `bitcoind`
cell is one verdict for the pinned release and for Core's `master`.

The invalid-`sendcmpct`, empty-`getblocktxn` and ignored rows read the
build's own `getnetworkinfo` `version`, and the pinned release carries
none of the changes they read, which each body asserts there instead. A
build carrying bitcoin/bitcoin@2d0dce0af54b8eb0ebdaf62f12a92d7e559a281e
drops the peer on the invalid-`sendcmpct` row, where the pinned release
keeps it. A build carrying
bitcoin/bitcoin@28641fd195db2a175fd43fee2e32758aef9816a6 drops the peer
on the empty-`getblocktxn` row, where the pinned release keeps it. A
build carrying bitcoin/bitcoin#32606 ignores, on the ignored row, a
`cmpctblock` from a peer that has sent no `sendcmpct`, and one it did
not ask for from a peer it has not selected for high-bandwidth mode,
where the pinned release takes each. Every other body whose check needs
the node to take a `cmpctblock` it did not ask for first has its peer
send a `sendcmpct` and deliver a block, so that the node selects it for
high-bandwidth mode.

`btclib-node`'s cell on each log row is a counted skip, and on the
outbound-`sendcmpct` and parallel-reconstruction rows a counted skip on
`TYPED_OUTBOUND`. Of the other rows asking for `MINE`, the ignored row
fails on the release, which takes a `cmpctblock` from a peer that has sent
no `sendcmpct`
([ISS btclib-node#1890](https://github.com/btclib-org/btclib-node/issues/1890)),
and passes on `main`, past
[ISS btclib-node#1897](https://github.com/btclib-org/btclib-node/issues/1897).
The rest pass: receiving a block as a `cmpctblock` and selecting a peer
for high-bandwidth mode
([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321));
announcing a new block as a `cmpctblock`, and reporting in
`getpeerinfo` a peer asking for that
([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223));
answering `getchaintips`
([ISS btclib-node#1393](https://github.com/btclib-org/btclib-node/issues/1393));
and, on the invalid-`sendcmpct` and empty-`getblocktxn` wire rows, dropping the
peer Core's `master` drops
([ISS btclib-node#1451](https://github.com/btclib-org/btclib-node/issues/1451),
[ISS btclib-node#1450](https://github.com/btclib-org/btclib-node/issues/1450)).

The `getblocktxn` row for a block near the tip passes.

`p2p_opportunistic_1p1c.py` is ported on it, its rows above each
one of Core's checks as a body over a fresh node in
`tests/integration/p2p_opportunistic_1p1c_test.py`, whose module
docstring has what differs from Core's file. Every body asks for
`ORPHANAGE` first, and for `MAXMEMPOOL`, `DATACARRIER` and `MINE`: its
node restarts with the `-maxmempool` Core's own starts with and a
`-datacarriersize` over the padding `mempool_util.fill_mempool` adds, which
a build without bitcoin/bitcoin#32406, first in `v30.0rc1`, refuses by
default, and `fill_mempool` fills its mempool. The parent-first,
low-and-high-child, multiple-parents and parent-in-mempool checks have
the node dial outbound full-relay peers, so they ask for
`TYPED_OUTBOUND`, and every check but the one chaining a package on
another asks for `CLOCK`. A `P2PK` row is its check over a parent with
no witness, Core's `RAW_P2PK` wallet. Each `bitcoind` cell is one
verdict for the pinned release and for Core's `master`. The rows marked
per-build read the build off its RPC: a build before `v30.0rc1`, the first
tag to carry bitcoin/bitcoin#31385 and bitcoin/bitcoin#31829, refuses a
child with its other parent where one parent is in the mempool, and bounds
the orphanage by count alone, evicting at random. On such a build the
parent-in-mempool row asserts the refusal Core's own `v29` file asserts,
the large-orphans row that no orphan is evicted, and the many-orphans row
that the orphanage fills to its bound and that its child is taken in with
its parent if still kept, and not if evicted. The parent-in-mempool row
reads `getnetworkinfo`'s `version`, bitcoin/bitcoin#31385 changing no RPC;
the others read `getorphantxs`'s `help`.
`ORPHANAGE` is declared
([ISS btclib-node#1420](https://github.com/btclib-org/btclib-node/issues/1420)),
so `btclib-node`'s cell on each row is a counted skip on a later capability
above.
Core's node starts with `-inboundrelaypercent` besides, an option the
pinned release refuses as unknown: the orphanage check sending many
orphans passes Core's own value only to a bitcoind whose
`getnetworkinfo` `version` reads at or past the first release carrying
the option, and asserts the same without it, the module docstring having
why.

`p2p_block_times.py` is ported on it, its row above, in
`tests/integration/p2p_block_times_test.py`, whose module docstring has
what differs from Core's file. Its body has the node dial an outbound
full-relay peer, so it asks for `TYPED_OUTBOUND`, and for `CLOCK` and
`MINE`, for Core's own mock time and the block Core's own mines to leave
initial block download. Its `bitcoind` cell is read per-build:
`getpeerinfo` reports `last_block_announcement` only on a build carrying
bitcoin/bitcoin#27052, which the pinned release does not, so the body
reads the build's own `getnetworkinfo` `version` and asserts, on an older
build, that the field is absent. `btclib-node`'s cell is a counted skip on
`TYPED_OUTBOUND`
([ISS btclib-node#1465](https://github.com/btclib-org/btclib-node/issues/1465)).

`p2p_outbound_eviction.py` is ported on it too, its rows above each one
of Core's checks as a body over a fresh node in
`tests/integration/p2p_outbound_eviction_test.py`, whose module docstring
has what differs from Core's file. Every body asks for `TYPED_OUTBOUND`,
`CLOCK` and `MINE`, and for `PEER_TIMEOUT`: its node restarts with
settings Core's own harness gives every node, a `-peertimeout` under
which the moved clock drops no peer as inactive, and automatic
connections off. Each `bitcoind` cell is one verdict for the pinned
release and for Core's `master`. `btclib-node`'s cell on each row is a
counted skip on `TYPED_OUTBOUND`.

The rest of the issue's own census is its later batches.

## Proxies: `Socks5Proxy`

[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47): a test
listens as a SOCKS5 proxy, points the node at it, and reads what the node asked
for. `socks5.Socks5Proxy` is that proxy, bound to loopback and accepting on a
thread of its own. It answers each `CONNECT` with success and queues a
`Socks5Request` -- the address type, the host, the port and any RFC 1929
credentials -- for `next_request`, then holds the connection open until `close`,
as Core's own `Socks5Server` does only under its `keep_alive` setting. The node
keeps the peer, and `getpeerinfo` lists it, until `close` or until the node's
own `-peertimeout` drops a peer that never answered. Given a
`destinations_factory`, as Core's own server is, it forwards each connection
where the factory names instead, or closes it where the factory names nowhere.
`socks5_test.py` drives it against a client written octet by octet. It listens
on IPv4 loopback, or on IPv6 loopback or a unix socket where its `family` asks,
and `endpoint` spells each the way `-proxy` takes it. `Capability.PROXY` is what
a test asks for: `-proxy`, with a `unix:` path, `-onion` and `-proxyrandomize`,
bitcoind's own flags. `Capability.PROXY_PER_NETWORK` is `-proxy`'s `=<network>`
suffix, which `v30.0rc1` is the first tag to carry (bitcoin/bitcoin#32425):
`BitcoindAdapter` declares it where the build's own `-help` shows the suffix.
`Capability.CJDNS`, `Capability.I2P_SAM` and `Capability.ONLYNET` are
`-cjdnsreachable`, `-i2psam` and `-onlynet`. `btclib-node` declares none of them
on any build: `cli.py` registers `-proxy`, and none of `-cjdnsreachable`,
`-i2psam` and `-onlynet`.

`feature_proxy.py` is ported on it, its rows above. Each of Core's
nodes is a test of its own; every start Core's file expects refused is
refused with Core's own wording whole, or, on a build without
`Capability.PROXY_PER_NETWORK`, a suffix start with that build's own port
refusal; and the restarts giving `-proxy` a network suffix compare every
network's proxy, where Core's file reads only the networks each names.
Those restarts are a counted skip on `Capability.PROXY_PER_NETWORK` where
it is not declared
([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)).
`tests/integration/feature_proxy_test.py`'s module docstring has what
differs from Core's file: among it, the start Core expects to succeed
with `-listenonion` on is dropped, since `BitcoindAdapter`'s own argv
turns it off. `btclib-node`'s cells are a counted skip on each row's own
capability.

`p2p_i2p_ports.py` and `p2p_i2p_sessions.py` need no proxy at all: each
gives its node an `-i2psam` endpoint nothing listens at, dials an I2P
address with `addnode`'s `onetry`, and reads Core's own line of the
node's `i2p` log category, which `BitcoindAdapter` enables
(`bitcoind.py`'s own `_command`). Each asks for `Capability.I2P_SAM` and
`Capability.DEBUG_LOG`, and keeps every step of Core's file in its order.
Each line is read once, as soon as `addnode` returns, as Core's own
`assert_debug_log` does by default:
`tests/integration/p2p_i2p_sessions_test.py`'s module docstring has why
that single read is what ties the persistent session's line to the dial.
`p2p_i2p_sessions.py`'s lines are read per-build: a build without
bitcoin/bitcoin#34051 omits `I2P` from them, so the body reads the build's own
`getnetworkinfo` `version`
([ISS 354](https://github.com/btclib-org/bitcoin-node-tests/issues/354)).
Both pins are Core's file at the pinned release too, and `btclib-node`'s
cells are a counted skip on `Capability.I2P_SAM`.

`p2p_dns_seeds.py` needs no proxy that answers either, and no DNS
server: its node is given Core's `UNREACHABLE_PROXY_ARG`, a `-proxy`
nothing listens at, under which a node querying a DNS seed resolves
nothing itself and queues a connection to the seed's name through the
proxy instead, while the peers it dials are on loopback, an address no
proxy is used for. It asks for `Capability.DNS_SEED`,
`Capability.KNOWN_ADDRESSES`, `Capability.PROXY`,
`Capability.TYPED_OUTBOUND` and `Capability.DEBUG_LOG`, and keeps every
step of Core's file over one node, in its order; each start Core expects
refused is refused with Core's own wording whole.
`tests/integration/p2p_dns_seeds_test.py`'s module docstring has what
differs from Core's file: among it, Core's `write_config` line turning
`-connect` off is passed on the command line, and its line turning
`-dnsseed` off is not. The pin is Core's file at the pinned release too,
and `btclib-node`'s cell is a counted skip on `Capability.DNS_SEED`.

`p2p_seednode.py` gives its node the same unreachable `-proxy`, so every
address the node dials and every seed node it asks is reached through a
proxy that is not there. It asks for `Capability.ADDRESS_FETCH`,
`Capability.KNOWN_ADDRESSES`, `Capability.PROXY`, `Capability.CLOCK` and
`Capability.DEBUG_LOG`, and keeps every step of Core's file over one
node, in its order, each reading the lines Core expects in the node's
debug log and the lines it does not: `assert_debug_log` (`debug_log.py`)
takes the second as Core's own `unexpected_msgs`.
`tests/integration/p2p_seednode_test.py`'s module docstring has what
differs from Core's file: among it, Core's `write_config` line turning
`-dnsseed` off is passed on the command line. The pin is Core's file at
the pinned release too, and `btclib-node`'s cell is a counted skip on
`Capability.ADDRESS_FETCH`.

`p2p_private_broadcast.py` is ported on the forwarding proxy, in
`tests/integration/p2p_private_broadcast_test.py`, whose module
docstring has what differs from Core's file. The factory reads each
connection's type off the node's own `getpeerinfo`, as Core's does, and
forwards the first private broadcast connection to a second node and
every other to a peer of the test's own, a `Listener` answering on a
thread of its own as Core's `P2PInterface` does. It asks for
`Capability.PRIVATE_BROADCAST` and the capability of every option its
node is given but `-test=addrman` and `-dnsseed` off, keeps Core's
steps in their order, and drops the last: Core restarts the node with
`-listenonion`, which `BitcoindAdapter`'s own argv turns off. Its pin is
past the pinned release, whose own file has no refusal of
`getprivatebroadcastinfo` and `abortprivatebroadcast` on a node without
`-privatebroadcast` and reads no `attempts_remaining`: the release's
binary answers neither way, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, what that
build answers instead. `btclib-node`'s cell is a counted skip on
`Capability.PRIVATE_BROADCAST`.

`p2p_private_broadcast_cap.py` is ported in
`tests/integration/p2p_private_broadcast_cap_test.py`, whose module
docstring has what differs from Core's file. Its node's `-proxy` and
`-i2psam` name a port nothing listens at, so no proxy runs. It asks for
`Capability.PRIVATE_BROADCAST`, `Capability.PROXY`,
`Capability.I2P_SAM` and `Capability.MINE`, and keeps every step of Core's
file in its order. A build before the cap puts none on the queue, the
file's whole subject, so the body reads `sendrawtransaction`'s `help` for
the sentence saying the queue is bounded, and asserts that the first
submission past the cap is refused exactly where the help carries the
sentence.
`p2p_private_broadcast_retry_v1.py` is ported on a forwarding proxy for
`-proxy` and another for `-onion`, in
`tests/integration/p2p_private_broadcast_retry_v1_test.py`, whose module
docstring has what differs from Core's file. The Tor proxy hands the
first IPv4 address it is asked for to a socket that reads the start of
what the node sends, and the body waits for a v2 start and then a v1
one. Core's file answers every other IPv4 connection through the Tor
proxy in BIP324's v2 transport, which `Peer` does not speak; the body
closes them instead. It asks for `Capability.PRIVATE_BROADCAST` and the
capability of every option its node is given but `-test=addrman` and
`-dnsseed` off. Core's file at the pinned release differs from the pin
in its factories' signatures alone.
`BitcoindAdapter` declares `Capability.PRIVATE_BROADCAST` only where the
build's `-help` lists `-privatebroadcast` (`bitcoind.py`'s own
`_has_private_broadcast`), so the private broadcast files are a counted
skip on a release whose `-help` lists none. `btclib-node`'s cell is a
counted skip on `Capability.PRIVATE_BROADCAST`.
`rpc_net.py`'s steps that need one node (`addnode`, a peer's service names,
`getnodeaddresses`, `addpeeraddress`, `getaddrmaninfo` and `getrawaddrman`) are
ported in `tests/integration/rpc_net_test.py`, each its own row. Its module
docstring has what differs from Core's file. Core gives its nodes a `-proxy`
nothing listens at, so that no step dials a public address; no step reads what
the node asks of it, so no proxy runs, and a step given the argument asks for
`Capability.PROXY`. The steps Core restarts with `-cjdnsreachable` ask for
`Capability.CJDNS`. A blank `addnode` address is refused only past the pinned
release, and a blank `addpeeraddress` address from `v31.0rc1` on. The body asks
the build a call that changes nothing and asserts that build's own answer. The
steps that connect Core's nodes are
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s.
`btclib-node`'s cells are a counted skip on each row's own capability.
`feature_config_args.py`'s steps whose subject is a proxy option (`-proxy`
given no value, `-connect` beside `-seednode` and `-dnsseed` and a proxy, and
`-privatebroadcast` without a Tor or I2P proxy, beside `-connect`, and beside
`-proxyrandomize` turned off) are ported in
`tests/integration/feature_config_args_test.py`, each its own row. Its module
docstring has what differs from Core's file. No step reads what the node asks
of a proxy, so no `Socks5Proxy` runs; each asks for `Capability.PROXY`, which
`btclib-node` does not declare, so its cells are a counted skip. The warning
of `-privatebroadcast` beside `-proxyrandomize` turned off ends in another
sentence before bitcoin/bitcoin@2630d8e6c9d6, which also adds a sentence to
`-privatebroadcast`'s `-help` text; the body reads that text and asserts the
build's own sentence. The file's other steps use a proxy only to keep the node
off the network, and stay with
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s list
above.

## The node wallet: `Capability.NODE_WALLET`

[ISS 45](https://github.com/btclib-org/bitcoin-node-tests/issues/45) holds
Core's tests whose subject is bitcoind's own wallet, every `wallet_*.py` file of
Core's `test/functional/` among them. A port of one that reaches the wallet runs
one body over both nodes, each wallet step behind `Capability.NODE_WALLET`
(`capability.py`). `BitcoindAdapter` declares it wherever its build carries the
wallet, `_has_wallet` (`bitcoind.py`) being the probe it shares with
`Capability.MINE`, and no other adapter declares it. btclib-node keeps no
wallet: `rpc/callbacks.py`'s dispatch table names no wallet RPC, so each such
port's `btclib-node` cell is a counted skip on it until
[ISS 199](https://github.com/btclib-org/bitcoin-node-tests/issues/199) gives the
btclib side a wallet to reach.

The adapter gains no method for it. A body creates the wallets it names
over `createwallet` and reaches each through `rpc.for_wallet(name)`,
`bitcoin_core_rpc`'s own client for `/wallet/<name>`, and
`BitcoindAdapter`'s own docstring has why every call names its wallet.
Each body starts a fresh node of its own (`bitcoind_cluster` or
`btclib_node_cluster`), so the
wallets it creates, and the option it restarts a node under, stay off
the node the session shares.

The `wallet_*.py` rows above are ported, every assertion of Core's own
kept. A row whose `btclib-node` cell is `skip (node_wallet)` asks one
node for its wallet and for nothing more than an option set at start,
`Capability.GENERATE`, `Capability.INVALIDATE_BLOCK`, `Capability.CLOCK`,
`Capability.PACKAGE_ACCEPTANCE` and `Capability.MINE`, and its file is
the same at the pinned release.
Each body module's own docstring (`tests/integration/<file>_test.py`)
has what of Core's harness it stands in for: where Core's harness pays
its coinbase to the deterministic key it imports into `default_wallet`,
the body mines to an address of that wallet's own instead; where the
harness creates no wallet to import the key into, the body mines to the
key's own address; where Core's `MiniWallet` spends a coin of the
harness's cached chain, the body's `MiniWallet` mines until a coin of
its own matures.

The rest of `wallet_*.py` waits on what each file asks beyond that,
among it: a second node; a restart with the wallet already on disk
(`wallet_startup.py`, `wallet_reindex.py`); an extended private key
built on the client (`wallet_createwallet.py`,
`wallet_listdescriptors.py`, `wallet_keypool.py`); an RPC the pinned
release does not have (`wallet_multisig_descriptor_psbt.py`'s
`derivehdkey`); a previous release
(`wallet_backwards_compatibility.py`); an external signer
(`wallet_signer.py`); or Core's `bitcoin-wallet` tool beside the clock
(`wallet_encryption.py`).

`wallet_disable.py` is a bitcoind-only row in `capability.py`'s own
sense, `-disablewallet` being bitcoind's own option, and it asks for no
capability at all: a build without the wallet accepts the option too.
`tests/integration/wallet_disable_bitcoind_test.py`'s own docstring has
how the pinned release's file differs from the pin.
