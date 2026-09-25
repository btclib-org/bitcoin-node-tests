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
which held it while tf2 had no repository of its own. Its prose is
unchanged by the move: a verdict names btclib's covering module because
btclib is what covers most of the directory today, this repository's own
adapter and test families being later steps of that same issue.

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
  meant to; this repository's own adapter and harness, later steps of
  ISS btclib-org/btclib#2220, are where it lands.
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

Verdict: **tf2's by decision**. ISS 1066, the same line.
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

Verdict: **tf2's by decision**. ISS 1066, the same line: an
authenticator written out by hand is what that issue put on tf2's side.

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
commit  3fd68a95e68b4c6f3bb6c59d41dd196001110f3a  2026-04-07
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered**, and wider than Core's file: `curves/curve.py`,
`curves/curve_group.py`, `curves/curve_group_2.py`,
`curves/curve_group_f.py` and `curves/sec_point.py` carry every curve
btclib has rather than secp256k1 alone. What the arithmetic is asserted
against is not a vector file but the `btclib_secp256k1` bindings, which
`curves.curve.mult` and its variants delegate to for secp256k1 and which
btclib's own suite validates the Python arm against. Core's file warns
that it is slow and side-channel vulnerable; btclib's `SECURITY.md`
publishes the same about its Python arm.

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

Verdict: **tf2's (harness)**. It fills and reads a running node's
mempool.

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
re-exported as `btclib.p2p.magic.magic_from_signet_challenge`, and its
own docstring states the rule in the same words Core's function
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
`btclib` names SOCKS nowhere.

### `test/functional/test_framework/test_framework.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/test_framework.py
commit  248ce46faf708a832b7922ae7ef9227dbcadf0e5  2026-09-22
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's (harness)**. The base class every functional test
derives from.

### `test/functional/test_framework/test_node.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/test_node.py
commit  d32a515fb0bbe7ce5be723ff37e532a8220bc3ce  2026-09-16
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
commit  6f4109b4489182bf5fa517630043df1829f00808  2026-08-25
behind  0 revisions; that commit is the tip of the path
```

Verdict: **covered in part**. `fee.fee_from_vsize` over a `FeeRate` is
what `get_fee` computes, and what `satoshi_round` quantizes to is what
`amount.py`'s `valid_btc_amount`, `sats_from_btc` and `btc_from_sats`
work in; `util_xor` went to tf2 with the compressor by ISS 1123. The
rest is the harness: the assertions, the ports, the datadirs, the
cookie files, the configuration files and the waits.

### `test/functional/test_framework/v2_p2p.py`

```text
repo    bitcoin/bitcoin
path    test/functional/test_framework/v2_p2p.py
commit  6a129983c9bf8efa1081f9a8b462c3635d1cfb39  2026-06-04
behind  0 revisions; that commit is the tip of the path
```

Verdict: **tf2's by decision**. ISS 1066 put BIP324's transport on tf2's
side. Its non-cipher halves are btclib's: `ecc/ellswift.py` is the key
exchange and `kdf.hkdf` the key schedule.

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
the node does not declare. bitcoind is the oracle (rule 3): a **fail**
on bitcoind is this repository's own defect rather than a finding for
another tracker.

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
| `p2p_block_sync.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_compactblocks_hb.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_getdata.py` | `aaf941202667` | 2026-07-31 | pass | fail ([ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)) |
| `p2p_invalid_locator.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_invalid_messages.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_invalid_messages.py` (log) | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `p2p_leak.py` (wire) | `01b8a117d2c5` | 2026-06-04 | pass | pass |
| `p2p_leak.py` (log) | `01b8a117d2c5` | 2026-06-04 | pass | skip |
| `p2p_net_deadlock.py` | `a0473442d1c2` | 2024-07-16 | pass | skip (raw_msg) |
| `feature_uacomment.py` | `fa5f29774872` | 2025-12-16 | pass | skip |

`feature_blocksdir.py`'s row is a smaller claim than Core's own test:
Core also mines blocks through the framework's own deterministic wallet
key before its disk read, which this drops -- a fresh node writes its
genesis block to `blk00000.dat` before anything is mined, so the
`-blocksdir` redirect this test is about needs nothing more than that
to show. btclib-node's cell names the capability rather than the
node's whole behaviour: a nonexistent `-blocksdir` is fatal there too,
passing the same way it does on bitcoind, and it is reading the chain
back in Core's own `blk*.dat` layout that is
`Capability.BLK_FILES` (`capability.py`) -- a capability btclib-node
never declares, not a gap its adapter is waiting on but the decision
[ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)
already closed on.

The refusal itself is matched against each node's own wording rather
than any early exit: bitcoind's own `Error: Specified blocks directory
"..." does not exist.`, the path double-quoted, on stderr; btclib-node's
own `btclib-node: specified blocks directory ... does not exist`, also
on stderr, lower-cased and without the trailing period or the quotes
bitcoind's carries.
`NodeAdapter.start` (`node.py`) reads a process's own stderr into the
`RuntimeError` it raises on an early exit, which is what the tests above
each check against
([ISS bitcoin-node-tests#19](https://github.com/btclib-org/bitcoin-node-tests/issues/19)).

`p2p_getdata.py`'s row is a smaller claim than Core's own test: Core
asks its "later valid `getdata`" question of a mined tip, and this asks
it of genesis instead, `Capability.MINE` not being every node's fact
yet. The invalid-`getdata`-then-`ping` half is unchanged from Core's.
Step 4 ([ISS bitcoin-node-tests#2](https://github.com/btclib-org/bitcoin-node-tests/issues/2))
re-asked whether that claim should widen now that `Capability.MINE`
exists: it does not, because the reason it was narrowed is unchanged --
`BtclibNodeAdapter` still does not declare `Capability.MINE`
([ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
is still open) -- and widening only the bitcoind half of this row would
leave its own column and btclib-node's answering a different question
about the same test.

The first family's own rows -- `p2p_block_sync.py`,
`p2p_compactblocks_hb.py`, `p2p_invalid_locator.py` and
`p2p_net_deadlock.py` -- are Core's own claim in full, `bitcoind`'s pass
being the whole of it: none narrows what Core asks, each needing
`Capability.MINE` (`p2p_block_sync.py`, `p2p_compactblocks_hb.py` and
`p2p_invalid_locator.py`, to reach a chain tall enough to mine or to
name) or `Capability.RAW_MESSAGE` (`p2p_net_deadlock.py`, Core's own
`sendmsgtopeer`) that `BtclibNodeAdapter` does not declare, so every
`btclib-node` cell is a counted skip rather than a run -- naming the
capability rather than the RPC, since a node offering the same fact
under another name would still answer `pass`. `p2p_compactblocks_hb.py`
identifies each of the node under test's own peers by connection order
rather than by the `-uacomment` Core's own `TestNode` sets, this adapter
carrying no per-node command-line option; every other assertion is
unchanged.

The log family's own rows (issue #5) are each half of one Core test
rather than the whole of it: `test_magic_bytes`
(`p2p_invalid_messages.py`) and the closing check of `P2PLeakTest`
(`p2p_leak.py`) each assert a disconnect *and* the log line Core's own
binary writes for it, and the charter's own rule for this family is
that a fact observable on the wire is asked for on the wire while a
fact only the log carries asks for `Capability.DEBUG_LOG` instead --
one mechanism, not one verdict, so the wire half and the log half of
the same Core test get their own row rather than being folded into a
single pass/skip that would hide which half a `skip` was ever about.
Neither ports the rest of its own Core file: `p2p_invalid_messages.py`'s
own other assertions need a mined chain or an option this step does not
register, and `p2p_leak.py`'s own earlier checks ask what a node sends
before a handshake completes, neither an `assert_debug_log` subject.

`feature_uacomment.py` is the option family's own first row
([ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)),
a smaller claim than Core's own test: Core's harness sets its own
`-uacomment=testnode{i}` on every node it starts, which this adapter
does not, so the default subversion carries no parenthetical comment at
all here rather than `(testnode0)`; the assertion this keeps is that a
comment appears once `-uacomment` names one. The length-limit and
unsafe-character checks are dropped -- both ask a node to fail its own
startup on a bad value, a mechanism this issue's own capability check
does not need and does not build. `Capability.UA_COMMENT`
(`capability.py`) is the shape rule 4's "a capability per option" takes
here: one member per Core option a ported test asks for, added the
moment that test is ported rather than for the whole of Core's option
surface up front -- `capability.py`'s own docstring has the case
against a single parameterized capability instead, and the charter's
own carve-out for a bitcoind-only option, which `-uacomment` is not.
`-uacomment` is not one of `cli.py`'s registered flags at `btclib-node`'s
current `main` (`btclib_node.py`'s own docstring has the measurement),
so this row's `btclib-node` cell is a counted skip.

No test measured for this family asks for an option `btclib-node` does
register (`cli.py`'s own `_build_parser`) and needs nothing else from
step 5, `MINE` or an outbound connection: `p2p_add_connections.py` is
the one dedicated `-maxconnections` test and needs `Capability.CONNECT`
throughout; `feature_discover.py`'s own `-discover` is neutered by this
adapter's own fixed `-bind` -- measured against the pinned bitcoind
binary, `getnetworkinfo`'s `localaddresses` answers empty whether
`-discover` is passed bare or given its own disabling value, so the
option has nothing to demonstrate under either adapter's own command
line. So this row exercises the skip
arm alone; the pass-through arm has no candidate yet, rather than one
being skipped over.

Most of the option family's remaining tests ask for another step-5
mechanism alongside an option -- MiniWallet, `assert_debug_log`,
`setmocktime` or the disk -- and are ISS 14's to port once every family
lands, not this issue's. Of the rest, most name a wallet feature or an
option only bitcoind has a reason to carry (`-torcontrol`, `-proxy`'s
own Tor/I2P half), which the charter's own rule keeps out of this
mechanism entirely. `btclib-node`'s own registered surface carries no
dedicated Core test that both asks for nothing else and does not already
write `bitcoin.conf` directly -- `rpc_whitelist.py` and `rpc_users.py`
set `-rpcauth` and `-rpcwhitelist` through the config file rather than
the command line, which is the disk family's own subject
(`datadir_path`/`bitcoin.conf`) and not this one's, and a string-literal
census such as ISS 3's own does not see a bare `key=value` config line
naming an option this way. `feature_reindex_init.py` shows a different
miss: the string literal `-test=reindex_after_failure_noninteractive_yes`
is what puts it in this family's own census, but the test also removes
`node.blocks_path / "index"` directly -- `blocks_path` being
`TestNode`'s own property name, a string the disk family's own
`datadir_path`/`blocks/` pattern does not match either -- so it needs
the disk family regardless of what `-test` itself turns out to name,
and belongs with ISS 14 rather than this one.
