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

A row whose subject is bitcoind's own option carries **bitcoind only**
in its `btclib-node` column instead: not a verdict on that node, since
no test of this shape ever runs against one. `capability.py`'s own
module docstring is the one place that states which options this
covers, and does not decide it row by row here.

A `btclib-node` cell may give a verdict on the build the row was
measured against and another on a later build, where the capability it
names is declared by a probe of the build rather than by the adapter's
class: the row's own paragraph below names the probe and the issue it
tracks.

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
| `rpc_whitelist.py` | `fa24693819e0` | 2026-05-26 | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `rpc_users.py` | `faf993ee4421` | 2026-05-26 | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `rpc_users.py` (`-norpcauth`) | same | same | pass | skip (rpc_auth_negation), [ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176) |
| `rpc_users.py` (`-rpcuser`/`-rpcpassword`) | same | same | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `rpc_users.py` (`-norpccookiefile`) | same | same | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `p2p_block_sync.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_compactblocks_hb.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_getdata.py` | `aaf941202667` | 2026-07-31 | pass | fail ([ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)) |
| `p2p_invalid_locator.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) |
| `p2p_invalid_messages.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_invalid_messages.py` (log) | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `p2p_invalid_messages.py` (inv, wire) | same | same | pass | fail ([ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)) |
| `p2p_invalid_messages.py` (inv, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (getdata, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (getdata, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (headers, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (headers, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (invalid pow, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (invalid pow, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (size, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (size, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (dup version, wire) | same | same | pass | fail ([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)) |
| `p2p_invalid_messages.py` (dup version, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (checksum, wire) | same | same | pass | fail ([ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)) |
| `p2p_invalid_messages.py` (checksum, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (msgtype, wire) | same | same | pass | fail ([ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)) |
| `p2p_invalid_messages.py` (msgtype, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 empty, wire) | same | same | pass | fail ([ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)) |
| `p2p_invalid_messages.py` (addrv2 empty, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 no addr, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 no addr, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 long, wire) | same | same | pass | fail ([ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)) |
| `p2p_invalid_messages.py` (addrv2 long, log) | same | same | pass | skip |
| `p2p_leak.py` (wire) | `01b8a117d2c5` | 2026-06-04 | pass | pass |
| `p2p_leak.py` (log) | `01b8a117d2c5` | 2026-06-04 | pass | skip |
| `p2p_net_deadlock.py` | `a0473442d1c2` | 2024-07-16 | pass | skip (raw_msg) |
| `feature_uacomment.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `rpc_uptime.py` | `406c2348ddbf` | 2026-06-13 | pass | skip (clock) |
| `feature_torcontrol.py` | `4556ef626754` | 2026-09-15 | pass, the `PoWDefensesEnabled` flag asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `p2p_bip434_feature.py` | `da74ff9ca49e` | 2026-06-04 | pass, `FEATURE`'s own disconnects asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `feature_framework_miniwallet.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip |
| `mempool_resurrect.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_spend_coinbase.py` | `6eca11175be6` | 2026-07-16 | pass | skip |
| `feature_dersig.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_dersig.py` (wire) | same | same | pass | skip |
| `feature_dersig.py` (log) | same | same | pass | skip |
| `feature_cltv.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_cltv.py` (wire) | same | same | pass | skip |
| `feature_cltv.py` (log) | same | same | pass | skip |
| `feature_csv_activation.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_dirsymlinks.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `feature_posix_fs_permissions.py` | `3fd68a95e68b` | 2026-04-07 | pass | fail ([ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198)) |
| `rpc_createmultisig.py` | `771200ca4362` | 2026-06-30 | pass | bitcoind only |
| `rpc_setban.py` (ban) | `fa21edddb272` | 2026-03-27 | pass | skip (ban) |
| `rpc_setban.py` (restart) | same | same | pass | skip (ban) |
| `rpc_setban.py` (non-IP) | same | same | pass | skip (ban) |
| `mempool_datacarrier.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_dust.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_sigoplimit.py` | `5d25a0c28d19` | 2026-07-07 | pass | skip |

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

`feature_filelock.py`'s row is a smaller claim than Core's own file: the
cookie- and PID-file persistence checks are dropped, being a fact about
which files a refused second start happens to leave behind rather than
about the lock itself, and the wallet-directory lock is dropped on the
charter's own "wallet ... tests stay out". What is kept whole is the
disk-family's own subject: a second process started over a datadir, or
a blocksdir, a first one already holds is fatal on both nodes, matched
against each one's own wording -- bitcoind's own "Cannot obtain a lock
on directory ...", a clean init error, and btclib-node's own uncaught
`Exception: IO error: While lock file: .../LOCK: Resource temporarily
unavailable`, measured live rather than a friendly message this node
does not write; the chainstate and the blocks databases are each their
own `Rdict` (RocksDB), which is what raises it, not a lock this adapter
or that one adds. That the second node crashes on an uncaught exception
rather than exiting the way Core's own init error does is
[ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147),
filed on that repository's own tracker (rule 3): the row's verdict stays
**pass** regardless, each node's stderr matched against its own wording
rather than against a shared shape.

`rpc_whitelist.py`'s row is a smaller claim than Core's own file: named
users exercising `rpcwhitelist` and `rpcwhitelistdefault` rather than
Core's own `strange_users` roster of malformed-input edge cases, a claim
about that file's own hand-written config parser rather than about
`rpcauth`/`rpcwhitelist`/`rpcwhitelistdefault` themselves, which is
`Capability.RPC_AUTH_CONFIG` (`capability.py`) -- the disk family's own
second capability, a `bitcoin.conf` key rather than a command-line
option, written to `datadir_path` before a node ever starts with no
adapter change needed. bitcoind declares it unconditionally;
`BtclibNodeAdapter` declares it per instance rather than at the class
level, and unlike every capability above this is not a fact about
`btclib-node` itself fixed once and for all -- `cli.py`'s own
`_RECOGNIZED_KEYS` already names `rpcauth`, `rpcwhitelist` and
`rpcwhitelistdefault` on `main`, landed as
[ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
alongside the module `btclib_node.py`'s own `_writes_auth_cookie` already
probes for cookie authentication; `__init__` declares the capability on
an instance exactly where that same probe answers `True`, both facts
landing in one commit. The build this repository's own
`TF2_BTCLIB_NODE_PYTHON` names, the PyPI release `btclib_node.py`'s own
docstring pins, predates that issue, so this row's `btclib-node` cell is
a counted skip against it; an instance built with an executable naming a
`main` build past #1070 declares the capability and runs the row's full
assertions, matched against `rpc_whitelist_bitcoind_test.py`'s own
claim.

`rpc_users.py`'s row shares `Capability.RPC_AUTH_CONFIG` and its
build-dependent cell with `rpc_whitelist.py`'s own row above, and is a
smaller claim than Core's own file in the same way. Kept: `-rpcauth`
authenticating a user given either through `bitcoin.conf` or on the
command line, a wrong password or a wrong user refused where a correct
one is accepted; `test_rpccookieperms`'s own POSIX permission bits
(`-rpccookieperms=owner`/`group`/`all`, and the default with none
given); a roster of Core's own malformed `-rpcauth` values, refused at
startup and matched against each node's own wording; Core's own
"interactions between blank and non-blank rpcauth" check, a blank
`-rpcauth=` refusing startup wherever it sits among named entries, in
every ordering Core's own file checks; and the "failure to write
cookie file will abort the node" check, a resource conflict in
the same shape `feature_filelock.py`'s own row is. `test_rpccookieperms`'s
own `platform.system() == 'Windows'` branch is dropped: this repository
gates on one image, `ubuntu-latest`
(`CONTRIBUTING.md`'s own table), so that branch is never reached here,
and the POSIX check is the whole of the row's own claim for it. The bare
`-rpcauth`, with no value at all, is dropped from the malformed roster:
it is `argparse`'s own "expected one argument" on btclib-node rather
than a fact about `RpcAuthEntry.parse` (`btclib-node`'s own
`rpc/auth.py`), which the roster's other values already exercise
between them. Core's own "-norpcauth disables previous -rpcauth params"
check is ported as its own test and its own row, gated on
`Capability.RPC_AUTH_NEGATION` rather than folded into the plain
`rpc_users.py` row's `RPC_AUTH_CONFIG` cell:
`-norpcauth` is not one of `cli.py`'s own registered flags on either
build measured, released or `main`, refused before a node ever starts
rather than accepted and disabling anything the way Core's own negation
does
([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)).
`BitcoindAdapter` declares the new capability unconditionally, the same
way it declares `RPC_AUTH_CONFIG`; `BtclibNodeAdapter` never declares
it, on either build, `cli.py` having no registered flag for the
`-norpcauth` row's `btclib-node` cell to become build-dependent on. That
cell is a counted skip on both builds, unlike the plain `rpc_users.py`
row's, which turns to a run past ISS btclib-node#1070.

Ported with `rpc_auth` (`NodeAdapter.__init__`): `-rpcuser`/
`-rpcpassword` and `-norpccookiefile`, gated on
`Capability.RPC_AUTH_CONFIG` on btclib-node too -- `cli.py`'s own
`_RECOGNIZED_KEYS` names both alongside `rpcauth` from the same commit
([ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)).
Dropped still: Core's own script-driven credential generation
(`share/rpcauth/`, run as a subprocess) and its `SystemRandom`-chosen
username, a claim about that script rather than about the mechanism,
matching `rpc_whitelist.py`'s own reason for dropping Core's
`strange_users` roster. Core writes no RPC cookie once `-rpcpassword`
is set or `-norpccookiefile` is given, `-rpcauth` present or not --
measured live against the pinned bitcoind, and against `btclib-node`'s
own `rpc/auth.py` docstring, which states the same rule for that node,
so `_rpc_client()`'s own default on both adapters, a cookie, waits on a
file the node configured either way never writes.
`NodeAdapter.__init__`'s own `rpc_auth` parameter (`node.py`) is what
makes this row's own port possible: the caller that configures a node
with either flag already knows the plaintext credential, and passes it
there instead of leaving the readiness wait on a cookie
([ISS bitcoin-node-tests#34](https://github.com/btclib-org/bitcoin-node-tests/issues/34)).
This is a smaller mechanism than Core's own `busy_wait_for_debug_log`,
an alternate readiness wait keyed on the debug log rather than RPC:
Core needs it because its own `test_norpccookiefile` pairs
`-norpccookiefile` with an `-rpcauth` value `test_framework/util.py`'s
own `get_auth_cookie` has no way to recover the plaintext of from
`bitcoin.conf` alone, where this repository's own tests construct every
`-rpcauth` value they use and so always hold the plaintext behind it.

A cookie the node cannot write is a different failure from a malformed
`-rpcauth`, and each answers with different wording on btclib-node:
a malformed `-rpcauth` is refused inside `cli.py`'s own `build_config`,
before a process is ever spawned, with `rpc/auth.py`'s own
`RpcAuthEntry.parse` raising "Invalid -rpcauth argument."; a cookie
write failure happens inside `Node.run`, once `rpc_manager.start_listener`
has already tried and failed, and `__init__.py`'s own `RPC_INIT_ERROR`
constant is bitcoind's own generic wording verbatim -- measured live, a
directory sitting where the cookie file must go refuses with `Error:
Unable to start HTTP server. See debug log for details.` on both nodes,
identically.

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
`p2p_leak.py`'s own earlier checks are not ported either way: they ask
what a node sends before a handshake completes, not an `assert_debug_log`
subject.

`p2p_invalid_messages.py` gains more rows of the same shape (issue #5),
one pair per Core assertion rather than one pair for the whole file:
`test_oversized_inv_msg`, `test_oversized_getdata_msg` and
`test_oversized_headers_msg` (each through the shared
`test_oversized_msg`), and `test_invalid_pow_headers_msg`, each a
`Misbehaving` log line paired with the disconnect it schedules.
`InvalidMessagesTest.set_test_params`'s own whitelist permission is
dropped for the same reason `test_magic_bytes`'s row already drops it:
`net_permissions.cpp`'s own parser reads the string ahead of the `@` as
a permission name, and the one Core's own file passes there grants
`NetPermissionFlags::Addr` rather than `NoBan`, so it does not exempt
the connection from the discourage-and-disconnect these checks are
about. `tests/integration/p2p_invalid_messages_misbehaving_bitcoind_test.py`'s
own docstring has the full argument, including why the PoW check needs
none of Core's own preliminary "send a valid header first" step. Of
these, only the oversized-`inv` row disagrees on btclib-node: its own
`p2p.callbacks.inv` returns before `Inv.parse` ever runs while the node
has not reached `NodeStatus.BlockSynced`, a status this adapter's own
peerless node never advances past, so an oversized announcement is
dropped unread rather than refused
([ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)).
The oversized-`getdata` and oversized-`headers` rows, and the
invalid-PoW row, reach `GetData.parse`, `Headers.parse` and
`assert_valid_pow` with no such guard in front of them, and pass.

`p2p_invalid_messages.py` gains a size row of the same wire-and-log
shape as `test_magic_bytes` (issue #5): Core's own `test_size` disconnects
the peer exactly as a wrong network magic does --
`V1Transport::readHeader` (`src/net.cpp`) refuses a header whose own
declared length is over `MAX_PROTOCOL_MESSAGE_LENGTH` and returns before
a message ever reaches `GetReceivedMessage`, the same early exit
`test_magic_bytes`'s own row already reads --
`tests/integration/p2p_invalid_messages_bitcoind_test.py`'s own docstring
carries both rows now. Both the wire and the log tests build the same
several-megabyte payload and tolerate a `ConnectionError` on the send
itself, measured live: the node closes the socket before this side has
finished writing it. btclib-node's own `frame_message` refuses the same
octets through `btclib.p2p.Message.parse`'s own length check ahead of the
network-magic one, so this row's `btclib-node` cell is `pass` on both
halves' own wire fact for the same reason `test_magic_bytes`'s already is.

More rows are the log family's own opposite wire fact:
`test_duplicate_version_msg`, `test_checksum` and `test_msgtype` (its
non-v2 branch, the only one this suite's `Peer` ever speaks) each reach
`V1Transport::GetReceivedMessage` (`src/net.cpp`), which sets
`reject_message` rather than returning early --
`CNode::ReceiveMsgBytes`'s own comment: "Message deserialization failed.
Drop the message but don't disconnect the peer." So each row's wire half
asks the opposite question from `test_magic_bytes`'s: that the connection
*survives*, read off a `ping`/`pong` round trip rather than
`wait_for_disconnect`.
`tests/integration/p2p_invalid_messages_dropped_bitcoind_test.py`'s own
docstring has the full argument, including why Core's own
`bytesrecv_per_msg` check on the checksum and msgtype rows is dropped.
Every one of them disagrees on btclib-node, and by a single shared
mechanism rather than a distinct one each: `Connection.run`'s own handler
around `frame_message` (`connection.py`) discourages and stops on *any*
`BTClibException`, where Core only logs and drops the one message --
`btclib.p2p.message._command_from_bytes` raises the identical exception
class for an invalid command that `Message.parse`'s own checksum check
does, so the checksum and msgtype rows are the same defect measured
again. [ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)
names it. The duplicate-version row fails for a different, adjacent
reason: `handle_p2p_handshake`'s own dispatch (`p2p/main.py`) discourages
and stops a `version`/`verack`/`wtxidrelay`/`sendaddrv2` arriving once the
connection is already `Connected`, ahead of the `version` callback's own
guard against a *pre-verack* repeat.
[ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)
names it.

Most of Core's own `test_addrv2_*` checks join the same shape, through a
raw `addrv2` message rather than through `btclib.p2p.AddrV2`'s own codec
-- `test_addrv2_empty`, `test_addrv2_no_addresses` and
`test_addrv2_too_long_address`, each asserting the connection survives a
malformed or trivial payload the way the rows above do.
`tests/integration/p2p_invalid_messages_addrv2_bitcoind_test.py`'s own
docstring has the full argument, including why `SenderOfAddrV2`'s own
explicit wait for the node's `sendaddrv2` needs no equivalent here: this
suite's `Peer.handshake` already negotiates `WTXID_RELAY_VERSION`, the
same floor BIP155's own `sendaddrv2` announcement is gated on.
`test_addrv2_empty` and `test_addrv2_too_long_address` disagree on
btclib-node, by a distinct but adjacent mechanism:
`btclib_node.p2p.callbacks.addrv2` calls `AddrV2.parse` with no
`try`/`except` of its own, and `handle_p2p`'s own `_drop` (`p2p/main.py`)
discourages and stops the connection for any `BTClibException` a
callback raises -- the dispatch-level path
[ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)
names, rather than the checksum and msgtype rows' own frame-level one.
`test_addrv2_no_addresses` raises nothing -- an empty list is valid --
so it passes on both nodes.

`test_addrv2_unrecognized_network` is not ported: Core's own assertion
needs bitcoind's own `Added ... addresses (of ...) from ...` line, which
is `LogDebug(BCLog::ADDRMAN, ...)` (`src/addrman.cpp`) rather than
`BCLog::NET`, and `BitcoindAdapter._command`'s own `-debug=net` is fixed
for the whole log family rather than adjustable per test. The one
`NET`-category line the same code path also writes, `Received addr: ...
addresses (... processed, ... rate-limited)`, does name a fact, but
measured live over several runs it always answers with the same address
processed and the other one rate-limited -- `peer.m_addr_token_bucket`'s
own address-rate limiter deciding which entry goes through and which is
deferred, not a fact about an unrecognized network or about `addrv2` at
all. A row asserting it would test this connection's own initial
token-bucket state rather than the claim `test_addrv2_unrecognized_network`
is about, so it stays open rather than being ported against an accounting
detail this test does not otherwise touch.

`p2p_bip434_feature.py`'s row is ported, narrowed to what a build lacking
BIP434 support disconnects for anyway rather than to `FEATURE`'s own
accepted shapes -- the length-boundary and acceptance checks Core's own
file also carries are `assert_debug_log` subjects the log family
(issue #5) already covers, not this row's -- and gated on a fact read
from the running build rather than assumed for the whole class
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35),
`capability.py`'s own module docstring): `node/protocol_version.h`'s own
`PROTOCOL_VERSION` constant, read at the pinned tag and at Core's
`master`:

```shell
gh api repos/bitcoin/bitcoin/contents/src/node/protocol_version.h?ref=v31.1 \
    -H 'Accept: application/vnd.github.raw' | grep PROTOCOL_VERSION
gh api repos/bitcoin/bitcoin/contents/src/node/protocol_version.h?ref=master \
    -H 'Accept: application/vnd.github.raw' | grep PROTOCOL_VERSION
gh api repos/bitcoin/bitcoin/contents/src/protocol.h?ref=v31.1 \
    -H 'Accept: application/vnd.github.raw' | grep -c FEATURE
```

confirms the pinned release's own gap -- `NetMsgType::FEATURE`
itself is absent from that tag's own header, landed only on `master`
afterward, in the same commit
(`6a129983c9bf8efa1081f9a8b462c3635d1cfb39`, "BIP434: FEATURE message
support") that bumped `PROTOCOL_VERSION` past the value the pinned tag's
own header carries -- so the version this row's test reads off
`getnetworkinfo`'s own `protocolversion` (or the p2p handshake's own
`version`, the same fact either way) is what decides which of `FEATURE`'s
own shapes to assert, rather than a version the pinned release happens
to be behind forever. Not a skip: a build with no `"feature"` branch at
all ignores the message exactly as it ignores any other one it does not
recognise, so the row's own tests assert that survival where a build
past the bump would disconnect instead --
`tests/integration/p2p_bip434_feature_bitcoind_test.py`'s own module
docstring has the rest of the narrowing, and why a skip was tried first
and reverted: `btclib-org/.github`'s own `reusable-integration-bitcoind.yml`
fails the required job on any skip its `exclude-classname` does not
name, one substring already spent on `btclib_node`. `doc/bips.md` at
Core's `master` names BIP434 as landing only in the next major release
after the one this repository pins, and the functional test itself
postdates the pinned tag (`da74ff9ca4`, 2026-06-04, not an ancestor of
it) -- so no release of the oracle this suite pins today ever sends or
accepts a `FEATURE` message, and this row's own assertion is what
answers for it instead of waiting for the pinned release to move: a
comment on
[ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5) says
this row need not wait either, since the informational `core-master` job
(`.github/workflows/node-integration.yml`,
[ISS 8](https://github.com/btclib-org/bitcoin-node-tests/issues/8))
already runs it against a build that does.

The log family's own census is wider than `p2p_invalid_messages.py` and
`p2p_leak.py`: re-run against Core's own current tip, `assert_debug_log`
also appears in several `p2p_*`, `feature_*`, `interface_*` and `rpc_*`
files that ask this step's charter for nothing else -- no option, no
`MiniWallet`, no `setmocktime`, no disk read -- the same sweep method
[ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5)'s
own re-derivation used against the option, MiniWallet, clock and disk
census lists above. None of them is examined here: this round's own scope
was `p2p_invalid_messages.py`'s remaining assertions and
`p2p_bip434_feature.py` alone, named as such rather than as the whole of
what the family still owes, and issue #5 stays open on that ground.

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

`rpc_uptime.py`'s row is Core's own claim in full: a single node,
`Capability.CLOCK` (Core's own `setmocktime`) the only fact it asks for,
so `btclib-node`'s cell is a counted skip on that capability rather than
a narrowed question.

`feature_torcontrol.py`'s row is the first of the bitcoind-only shape
[ISS bitcoin-node-tests#23](https://github.com/btclib-org/bitcoin-node-tests/issues/23)
builds: `-torcontrol`, the charter's own second named example of an
option only bitcoind has a reason to carry, drives a real handshake
against a mock Tor control server this test carries alongside itself
rather than in this repository's own harness. A smaller claim than
Core's own file, declared rather than silent: Core's own mock server
negotiates proof-of-work defenses on `ADD_ONION`, a step `src/torcontrol.cpp`
at the pinned release's own tag never takes and Core's own `master`
always does, landed in between the pinned tag and `master` in
`4c6798a3d386c2c1a4bcc4a8694281a8f0bef92d` -- read from the running
build rather than assumed for the whole class
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35),
this table's own paragraph above), so this row's own test asserts
whichever of the pinned tag's and `master`'s own shapes the build under
test actually carries, off `getnetworkinfo`'s own `version`.
`tests/integration/feature_torcontrol_bitcoind_test.py`'s own module
docstring has the measurement, both builds' own `version` included.
Kept whole: the sequence from
`PROTOCOLINFO` through `ADD_ONION` a fresh onion service takes to come
up. No other option of
the first family's or the option family's own census names a fact only
bitcoind's binary can answer without also asking for a mechanism this
repository does not build -- `-disablewallet`, the charter's own other
example, is a wallet feature by name and stays out on that ground alone;
`-proxy`'s own Tor/I2P half needs the SOCKS5 harness `TF2.md`'s own
framework-file ledger already marks `tf2's (harness)`, not built yet
either.

Re-run against Core's own current tip rather than the census's own
`cff00c5`, the family's own census gains one candidate neither of the
paragraphs above names: `p2p_compactblocks_blocksonly.py`. `-blocksonly`
is on neither adapter's own registered surface (`btclib-node`'s `cli.py`,
checked against both the pinned PyPI build and its own `main`), and
every other fact the test asks for -- `Capability.MINE`,
`Capability.CONNECT`, and a raw peer connection -- is already the
adapters' own rather than a step 5 mechanism, so this is the option
family's own second candidate rather than ISS 14's. It is not the same
shape `p2p_compactblocks_hb.py` already ported, though: Core delivers
each block itself, over a synthetic connection it controls, so the peer
whose `sendcmpct` renegotiation is under test is fixed rather than
raced for one of several slots -- measured live against a pair of
`BitcoindAdapter`s joined by `connect_nodes` instead, `bip152_hb_to` and
`bip152_hb_from` stayed `False` on both sides through several relayed
blocks, so the `getpeerinfo` shortcut `p2p_compactblocks_hb.py` used
does not carry this row. It wants `peer.py`'s own wire instead --
BIP152's `sendcmpct` and `cmpctblock`, which `btclib.p2p.compact_blocks`
already carries -- and stays open under this issue.

`rpc_echo_payload.py` is the family's other open candidate. Its subject
is an RPC server's own, not bitcoind's alone: a payload of any size is
either answered or refused, never left to time out, with `-rpcworkqueue`
and `-rpcthreads` set low only so that concurrent callers fill the queue.
Another node's RPC server could make the same promise, so the options
are a capability `btclib-node` does not declare yet (neither is in its
`cli.py`), not a bitcoind-only row, and the test stays open under this
issue. Core's test sends each payload through `echo` or through
`sendrawtransaction`, chosen at random; `btclib-node`'s
`rpc/callbacks.py` has the second and not the first, so a port also
needs `echo`, and accepts a refusal in the node's own wording rather
than Core's `Work queue depth exceeded`.

Of the rest of the family's own census, string-literal matches and
nothing more: `feature_bind_extra.py` and `rpc_bind.py` read the
sockets a running node has actually bound, over `lsof`
(`test_framework.netutil.get_bind_addrs`), a fact no step 5 family
names a mechanism for; `feature_bind_port_discover.py` and
`feature_bind_port_externalip.py` need a routable, non-loopback address
already configured on the host's own network interface, which the CI
environment they were written for provides and this repository's own
harness does not; `feature_help.py` reads a node's own stdout before
its RPC ever answers, which `NodeAdapter.start` (`node.py`) never
captures; `interface_gui.py` needs `bitcoin-gui`, a binary the pinned
release this repository fetches does not carry;
`feature_framework_startup_failures.py` relaunches Core's own Python
harness to test its exception handling, never a node; and
`tool_bench_sanity_check.py` sets `self.num_nodes` to none at all,
swept in by the census's own file-prefix regex rather than by anything
a node does.

A further group of files scores option-family, single mechanism on the
census's own reading, and each turns out on a closer one to need a
mechanism this issue does not deliver -- named here rather than ported,
each against the issue that owns what it is missing.

`feature_prune_stale_fork.py` (`-prune`, `-fastprune`) builds a stale
fork the same way `mini_wallet.py`'s own `build_fork` does -- a
header-only parent over `submitheader`, a full child over
`submitblock` -- prunes it and restarts, which is Core's own subject.
Reproduced against the pinned release, the sequence crashes the oracle
itself with `Assertion failed: (!foundInUnlinked)`
(`validation.cpp`'s own `CheckBlockIndex`): bitcoin/bitcoin's own
[ISS 35050](https://github.com/bitcoin/bitcoin/issues/35050), fixed on
`master` at bitcoin/bitcoin@fb47793b99f71f00a93339b88d1e2d7b5afa8e73
before the pinned release was tagged but never backported into it.
Rule 3's oracle is not authoritative on this one file until the pin
names a release carrying that fix --
[ISS 62](https://github.com/btclib-org/bitcoin-node-tests/issues/62).

`rpc_validateaddress.py` (`-prune`) sets `self.chain = ""`, Core's own
main chain: its subject is `validateaddress`'s own bech32/base58 error
wording, which differs by network, and neither adapter's own `_command`
can start a node on anything but regtest -- `BitcoindAdapter`'s own
hardcodes `-regtest`, and appending `-chain=main` through `extra_args`
reaches bitcoind's own argument parser rather than the adapter, which
refuses the combination outright. Not a capability a node can lack and
skip: neither node can be asked to start this way at all --
[ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63).

`feature_nulldummy.py` (`-testactivationheight=segwit@N`,
`-addresstype=legacy`) is NULLDUMMY compliance itself: a bare-multisig
scriptSig's own dummy element, built with `createmultisig`/
`createrawtransaction`/`signrawtransactionwithkey` and hand-tampered
before and after activation. `MiniWallet` spends only its own fixed
`ADDRESS_OP_TRUE` leaf by design (`mini_wallet.py`'s own docstring, and
rule 7 of [ISS btclib-org/btclib#2220](https://github.com/btclib-org/btclib/issues/2220)
already leaving btclib's own signing surface to btclib's own suite), so
nothing here builds a transaction carrying a caller-chosen script --
narrowing this file the way `feature_cltv_bitcoind_test.py` narrows its
own closing checks would leave nothing NULLDUMMY-specific behind --
[ISS 64](https://github.com/btclib-org/bitcoin-node-tests/issues/64).

`feature_versionbits_warning.py` (`-alertnotify=<cmd>`) and
`rpc_signer.py` (`-signer=<cmd>`) each start a node that execs an
external command -- a shell one-liner writing to a file, a bundled mock
signer script -- and assert on what that process did. No adapter here
runs, tracks or verifies an external process a node itself spawns; both
are
[ISS 49](https://github.com/btclib-org/bitcoin-node-tests/issues/49)'s
own subject, "drives another binary", rather than this issue's.

`feature_presegwit_node_upgrade.py` (`-testactivationheight=segwit@N`)
stops the node, expects a lower `-testactivationheight=segwit@N` to
refuse to start with a named init error, then starts it again with
`-reindex` added to that same lower height -- each restart naming
`extra_args` other than the ones the node last held.
`NodeAdapter.restart` (`node.py`) restarts only over the `extra_args` a
node was constructed with;
[ISS 51](https://github.com/btclib-org/bitcoin-node-tests/issues/51) is
what a restart naming a different argv needs.

`feature_framework_miniwallet.py`'s own row is the MiniWallet family's
first ([ISS bitcoin-node-tests#4](https://github.com/btclib-org/bitcoin-node-tests/issues/4)),
and a smaller claim than Core's own file: `mini_wallet.py`'s own
`MiniWallet` carries one of Core's own modes, the default
`ADDRESS_OP_TRUE` -- a P2TR output whose internal key and single
tapscript leaf `mini_wallet.py`'s own docstring has, needing no minimum
scriptSig size or mempool policy flag `RAW_OP_TRUE` would -- and this
row asks only the subject the issue is about: a coin mined without a
node's own wallet, cached with no `scantxoutset`, and spendable. Dropped
along with Core's other modes are `target_vsize` padding
(`test_tx_padding`) and a second, tagged wallet instance
(`test_wallet_tagging`), neither bearing on how the cache is fed.

`Capability.MINE` is what this row's `btclib-node` cell skips on, the
same shape the first family already takes rather than a new question:
`mini_wallet.py`'s own mechanism produces exactly the fact `MINE` already
names -- "a block the node accepts as its own new tip, however it gets
there" -- by client-side construction over `submitblock` rather than a
node's own wallet. No wire-only delivery avoids the skip:
`btclib_node.py`'s own docstring already measured why a solo
`btclib-node` never leaves `NodeStatus.SyncingHeaders`
([ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071))
-- a block it is handed never becomes its own tip whether it arrives over
`submitblock` or the wire, the gap being the node's own state machine and
not how the block is delivered.

The census [ISS btclib-org/btclib#2135](https://github.com/btclib-org/btclib/issues/2135)
counted is re-measured here, against Core's `test/functional/*.py` at
`f6b19b19` (2026-09-25), asking that issue's own name-set of each file
whether MiniWallet is the *whole* of what the file asks a node for rather
than one mechanism among several. This file answers yes, and so do
`mempool_accept_wtxid.py`, `mempool_resurrect.py`,
`mempool_spend_coinbase.py`, `mining_template_verification.py`,
`rpc_generate.py`, `rpc_orphans.py`, `rpc_scantxoutset.py` and
`rpc_signrawtransactionwithkey.py` --
[ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4)'s own
remaining ports, not
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s,
once this row's mechanism lands.

Reading the census's own remaining files against Core at the pins in
their own rows or paragraphs below leaves that census whole: every file
it names is still this issue's, several needing more than this round
builds.

`mempool_resurrect.py` and `mempool_spend_coinbase.py` are ported, their
own rows above: `mini_wallet.py`'s own `get_utxo` (a cached coin by its
own txid, maturity aside), `create_self_transfer` and `send_self_transfer`
(`utxo_to_spend`, spending a caller-named coin in place of the next
automatically matured one) and `resync` (re-reading the tip after a chain
move this wallet did not itself make) are what `mempool_spend_coinbase.py`
needed and `build_fork` (Core's own `create_empty_fork`, `blocktools.py`)
is what `mempool_resurrect.py` needed beyond the mechanism above, each
added to `mini_wallet.py` and unit-tested against the fake RPC.
`mempool_resurrect.py`'s own reorg is a fork long enough to outweigh the
chain this port also mines meanwhile -- `_FORK_LENGTH`, the integration
module's own constant, narrower than Core's own fixed margin over its
own intervening blocks, both clearing the same requirement: more work
than what gets reorged away. `mempool_spend_coinbase.py` reaches the
same mature/immature boundary by mining exactly `COINBASE_MATURITY`
blocks from a chain that starts at height zero, rather than
`invalidateblock`ing blocks off the chain Core's own fixture already
starts every test deep into; this node carries no such fixture, so this
port never calls `invalidateblock` at all, a narrower claim than Core's
own file in the RPCs it exercises, not in the boundary it checks.

`rpc_generate.py`, `rpc_scantxoutset.py`, `rpc_signrawtransactionwithkey.py`
and `mining_template_verification.py` stay open under this issue, as the
census above has them. Each drives
`generatetoaddress`/`generateblock`/`generate`, `scantxoutset`,
`signrawtransactionwithkey`, or `getblocktemplate` in proposal mode as
its own subject, `MiniWallet` only funding a transaction
the RPC under test then answers for. None of those RPCs is in
`btclib_node`'s own dispatch table (`src/btclib_node/rpc/callbacks.py`).
A port's `btclib-node` cell is the family's own skip on `Capability.MINE`
all the same, so the missing RPC is a finding on btclib-node's tracker
only once that node declares `MINE`.

`mempool_accept_wtxid.py` needs `MiniWallet.create_self_transfer` plus a
script-malleation helper this repository does not yet build -- Core's own
`build_malleated_tx_package` (`test_framework/script_util.py`), a pair of
children of one parent sharing a txid and differing only in the witness
that satisfies it -- and a peer connection watching which one the node
rebroadcasts by wtxid. `rpc_orphans.py` needs
`create_self_transfer(utxo_to_spend=...)` chained into orphan pairs,
`getorphantxs` (absent from `btclib_node`'s own dispatch, so `bitcoind
only` the way `feature_torcontrol.py`'s row already is), and separate
`peer.py` connections, each sending an unconfirmed child ahead of its own
parent. Both ask for MiniWallet alone in step 5's own sense -- no node
wallet, no log, no mocktime, no disk, one node, no option beyond the
adapters' -- so
neither is ISS 14's; both stay open under this issue, unported this
round.

`mempool_cluster.py` and `rpc_packages.py` also drive MiniWallet alone at
first read, but each also restarts its node with an option --
`-limitclustersize`/`-limitclustercount` and
`-maxmempool`/`-persistmempool` in turn -- that `btclib-node`'s own
`cli.py` does not register, so the option family's own exclusion reaches
them too: ISS 14's, same as the wallet, log, disk and clock files below.
`mempool_sigoplimit.py`, named alongside them for the same reason, is
ported below, its own paragraph naming what of it is kept.

`p2p_tx_privacy.py` (also pinned `fa5f29774872`) asks for MiniWallet
alone too, driving a second p2p connection of its own alongside the
first -- one held back from completing its handshake while the other
already sends a transaction -- to assert a `wtxid` announcement is
withheld from the second until its own handshake completes. `peer.py`'s
own `handshake` is one blocking call from open to `verack`, with no step
in between for a caller to hold a second connection at; unported for
that reason, and left to ISS 14 once step 5 gives it one. Every other
MiniWallet-touching file asks for a wallet (`createwallet`, out for good,
rule 3's own exclusion), the log, the disk or the clock alongside
MiniWallet, or an option -- ISS 14's once every step-5 mechanism lands,
the wallet files excepted.

`feature_dersig.py`, `feature_cltv.py` and `feature_csv_activation.py`
are ISS 14's own softfork-activation-height trio, the option and
MiniWallet families' first tests to need both mechanisms together:
`-testactivationheight=<deployment>@<height>` (`Capability.TEST_ACTIVATION_HEIGHT`,
`capability.py`) holds one buried deployment inactive until a chosen
height, and `MiniWallet.generate` (`Capability.MINE`) mines to it with
no node wallet. Each is a smaller claim than Core's own file, declared
rather than silent, its own `*_bitcoind_test.py` module docstring
carrying the full argument: kept is `getdeploymentinfo`'s own transition
one block before the configured height, and, for `feature_dersig.py`
and `feature_cltv.py`, the buried-deployment version floor a too-low
block version trips once the deployment is active -- `bad-version(0x...)`,
`submitblock`'s own answer and, on a row of its own, the same wording in
bitcoind's own debug log. Dropped from every one of them: every check
needing a real signature or a caller-chosen tapscript leaf --
`feature_dersig.py`'s own non-DER signature, `feature_cltv.py`'s own
`OP_CHECKLOCKTIMEVERIFY` failure reasons, and the whole of
`feature_csv_activation.py`'s own body, BIP68's relative locktimes,
BIP112's `OP_CHECKSEQUENCEVERIFY` and BIP113's median-time-past cutover
included -- `MiniWallet`'s own `ADDRESS_OP_TRUE` coins spend through one
fixed tapscript leaf carrying neither opcode, and building one that does
is a capability neither this trio nor the mechanisms it already
combines reaches; each of these checks stays open under this issue.
`feature_csv_activation.py` gains no version-floor row the way its
siblings do: `src/validation.cpp`'s own `ContextualCheckBlockHeader`
reads only `DEPLOYMENT_HEIGHTINCB`, `DEPLOYMENT_DERSIG` and
`DEPLOYMENT_CLTV` for its version check, `DEPLOYMENT_CSV` never joining
it, so there is no such refusal for CSV's own activation to produce.
Every `btclib-node` cell across the trio is a counted skip on
`Capability.TEST_ACTIVATION_HEIGHT` alone, ahead of `Capability.MINE`
which every row also needs: measured against `cli.py`'s own
`_build_parser`, `-testactivationheight` is not one of its registered
flags on the build this repository's own `TF2_BTCLIB_NODE_PYTHON` names,
so `require` never reaches the second capability at all.

`feature_dirsymlinks.py`'s row is Core's own claim in full
([ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7),
found by [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
census, disk-family mechanism alone): a node restarted over `blocks/`
and `chainstate/` each replaced by a symlink to elsewhere starts exactly
as it does over the plain directories, `NodeAdapter.start` (`node.py`)
answering the same way whichever the OS resolves the path to. No
`Capability` is asked for, the fact being about the operating system's
own symlink resolution rather than about either node's own storage
format; measured live, both `bitcoind` and `btclib-node`'s own RocksDB
stores open through the symlink unchanged.

`feature_posix_fs_permissions.py`'s row is a smaller claim than Core's
own file ([ISS 7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)):
the `wallets_path` permission check is dropped on the charter's own
"wallet ... tests stay out" (step 5 of issue btclib-org/btclib#2220) --
this repository starts no node wallet, so no `wallets/` directory of a
node's own ever exists to check the permissions of. Kept whole: the
node's own chain directory and its own log file refuse every permission
bit but the owner's own read, write and, for the directory, execute. No
`Capability` is asked for either -- the fact is not that `btclib-node`
lacks a mechanism, but that it sets one it already has (a directory's
own mode) differently from bitcoind, which is a disagreement rather than
a missing capability. Measured live against `btclib-node` `main`
`b853eb46`: the chain directory and every store directory under it, and
`history.log` (`btclib_node.py`'s own `log_path`, the fact
`debug_log_path` names for bitcoind), all come up at the operating
system's own umask default -- group and other readable, the directories
executable too -- rather than an owner-only mode either the directory
creation or the store construction sets. Filed as
[ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198).

`rpc_createmultisig.py`'s row is a smaller claim than Core's own file
([ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4),
found by [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
census): Core's own file asks both that `createmultisig` construct the
right address, redeemScript and descriptor, and that the address it
constructs is actually spendable, through
`signrawtransactionwithkey` and `combinerawtransaction` assembling real
ECDSA signatures over a `MiniWallet`-funded coin. Only the first is
kept: `MiniWallet`'s own coins carry no signature at all
(`mini_wallet.py`'s own docstring), so a spend of a multisig output
built for real keys is not a claim this repository's own mechanism can
make, and rule 7 of issue btclib-org/btclib#2220 leaves btclib's own
signing surface to btclib's own test suite. Dropped for that reason:
`do_multisig`'s own spend/sign/combine/broadcast body,
`test_combinerawtransaction_preconditions`, and
`test_mixing_uncompressed_and_compressed_keys` (a claim about a spend's
own address fallback, the same reason). Dropped for a second reason,
independent of the first: `ScriptPubKey.p2ms` (`btclib.script.script_pub_key`)
refuses a bare multisig script naming more keys than `OP_CHECKMULTISIG`'s
own key count can hold pushed as a small integer, `OP_16` being the
largest one a script has, by construction -- so `test_multisig_script_limit`'s
own past-that-limit cases, and the "correct encoding" check past the
same bound, have no btclib construction to compare bitcoind's own answer
against; the "correct encoding" check is kept up to `OP_16`'s own bound
instead. Dropped for a third reason:
`test_sortedmulti_descriptors_bip67` reads its vectors from Core's own
`data/rpc_bip67.json`, a vendored fixture this repository does not
carry. What is kept -- `createmultisig`'s own construction, across
every `(nsigs, nkeys, output_type)` Core's own `m_of_n` list names, the
encoding check up to `OP_16`'s own bound, and the `bech32m` refusal --
needs no coin, no mining and no node wallet, so the row carries no
`Capability` at all.
`createmultisig` is not in `btclib_node`'s own dispatch table
(`src/btclib_node/rpc/callbacks.py`, measured at `main` `b853eb46`), the
same "bitcoind only" shape `feature_torcontrol.py`'s own row already
takes for a fact no other node under this repository's reach offers, so
this module has no `_btclib_node_test.py` counterpart.

[ISS 6](https://github.com/btclib-org/bitcoin-node-tests/issues/6)'s own
remaining files, `p2p_fingerprint.py` and `p2p_invalid_block.py`, are
not in this batch: each needs `Capability.MINE` and a raw peer
conversation well beyond a handshake -- `p2p_fingerprint.py` a
headers-first reorg onto a fork built and held back rather than
submitted, `p2p_invalid_block.py` a legacy `OP_TRUE` bare coinbase and
scriptSig distinct from `MiniWallet`'s own P2TR shape, plus merkle-root
malleability and a `getdata`-driven send/reject cycle matched against
`Capability.DEBUG_LOG`'s own wording. Neither mechanism is this batch's
to build; both stay open under [ISS 6](https://github.com/btclib-org/bitcoin-node-tests/issues/6)
for a later one, as its own comment already said they would.

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
`btclib-node` declares neither, on either build measured: `BAN` is
already [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088);
`DISCONNECT` is new, filed as
[ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193).

**A real finding, from building the mechanism rather than from reading
about it**: `connect_nodes`'s own `addnode ... "onetry"` left bitcoind's
own `v2transport` argument unset -- harmless between a pair of
`BitcoindAdapter`s, both defaulting the same way, but fatal the moment
`first` is a `BitcoindAdapter` dialling a `BtclibNodeAdapter`: bitcoind's
own `debug.log` read "start sending v2 handshake" immediately followed
by "socket closed, disconnecting", and the handshake wait timed out. No
test built before this issue ever dialled one kind of node from the
other, so nothing had exercised this path. bitcoind itself never falls
back to v1 once a v2 attempt is reset by the other side
([ISS btclib-node#1197](https://github.com/btclib-org/btclib-node/issues/1197)),
so `connect_nodes` now passes `v2transport` explicitly rather than
leaning on a fallback, matching Core's own `connect_nodes`'s
`peer_advertises_v2` parameter, here with a default of `False`, the one wire
every adapter this repository builds speaks -- `btclib-node`'s own
`add_node` reads and type-checks the argument without ever acting on it,
[ISS btclib-node#1190](https://github.com/btclib-org/btclib-node/issues/1190)
being why. A test whose subject is BIP324 itself,
`v2transport_option_bitcoind_test.py`, passes `True`. Measured against
the fix: the mixed-cluster test below, which timed out before it and
passes after, on every `btclib-node` build measured.

`rpc_setban.py` is ported, its own rows above. Core's own file restarts
a node repeatedly, some of those with different `extra_args` than it
started with and some with the same. The different-`extra_args`
restarts -- the `-whitelist` noban-permission section and the
`-bantime` persistence section -- are a mechanism `NodeAdapter.restart`
(`node.py`) does not offer, reusing the constructor's own `extra_args`
unconditionally, and no family of this repository has needed that yet;
both sections are dropped rather than building it here, out of this
issue's own charter, and filed as
[ISS bitcoin-node-tests#51](https://github.com/btclib-org/bitcoin-node-tests/issues/51).
The same-`extra_args` restarts are ported, `restart` already offering
exactly that: a ban surviving a plain restart, checked through
`connect_nodes`' own handshake wait timing out on a still-banned dial
rather than through Core's own `assert_debug_log` (a capability this
repository does not have yet), and reconnection succeeding again once
the ban is lifted. Kept alongside them: a live connection dropping the
moment `setban` matches its address, `node.wait_until_disconnected`
standing in for Core's own wait on `is_connected_to` going false; and
the non-IP address check, which needs no second node at all.
`Capability.BAN` is `btclib-node`'s counted skip on every row, on every
build measured.

A cluster mixing bitcoind and btclib-node -- the issue's own "most
valuable case" -- is `tests/integration/conftest.py`'s new
`mixed_cluster` fixture: one fresh node of each kind, started
independently and left to a test's own `connect_nodes` to wire together,
matching `bitcoind_cluster`'s own shape.
`tests/integration/mixed_cluster_block_sync_btclib_node_test.py`
exercises it: bitcoind mines, and btclib-node -- never asked to mine
anything itself -- receives the block over a real connection and its own
tip converges. Not a per-test ledger row: no Core file poses this
question, Core's own tests running one binary against copies of itself.
**Passes on every `btclib-node` build measured** -- the released PyPI
build `btclib_node.py`'s own docstring pins, and `main` at `d98bd7d6` --
the v2transport fix above is what this needed, not `Capability.MINE`,
which `btclib-node` still does not declare
([ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)):
nothing here asks the connecting side to mine anything of its own.

Re-run against btclib-node's own `main` (`d98bd7d6`) rather than only the
released build: `p2p_invalid_messages_dropped_btclib_node_test.py`'s
msgtype, checksum and duplicate-version rows,
`p2p_getdata_btclib_node_test.py`'s row, and
`p2p_invalid_messages_misbehaving_btclib_node_test.py`'s oversized-`inv`
row now pass -- [ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130),
[ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133),
[ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)
and [ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)
each fixed there since. `p2p_invalid_messages_addrv2_btclib_node_test.py`'s
addrv2-empty and addrv2-long rows still fail on `main`,
[ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)
still open. This table keeps the released build's own verdicts, per its
own reading rules above; the `main` job
(`node-integration.yml`'s own `btclib-node-main`) is what this
observation came from, and it gates nothing (`CONTRIBUTING.md`'s *What
gates a merge, and what only reports*).

Of the issue's own census list, the mechanism no longer blocks
`interface_rest.py` (option, MiniWallet, disk, plus `sync_all` across a
pair of nodes) or `mining_getblocktemplate_longpoll.py` (the log family,
MiniWallet, plus a node observing another's mined block over real
propagation) on that ground alone -- each still needs its own read
against the option, MiniWallet and log families' own open issues
([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3),
[ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4) and
[ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5))
before it can be scheduled, not having had one this round.
`rpc_txoutproof.py` needs `sync_txindex`, Core's own wait for a
`-txindex` to catch up, which is a different primitive from
`wait_until_tips_agree`/`wait_until_mempools_agree` and is not built by
this issue. `p2p_disconnect_ban.py`'s own remaining "Test disconnectnode
RPCs" section -- everything but the `setban`/banlist half this round
left aside -- needs nothing this issue does not already provide, and is
this repository's own next-smallest candidate. `feature_assumeutxo.py`
stays disqualified on the sixth thing the census already named: a
background IBD racing a live feed, which no mechanism here builds.
`feature_fee_estimation.py`, `mempool_reorg.py`, `mining_basic.py`,
`p2p_segwit.py`, `feature_bip68_sequence.py` and `rpc_rawtransaction.py`
were not re-read this round and stay open exactly as the census left
them. `p2p_v2_transport.py` stays blocked on BIP324 itself, which
neither adapter speaks
([ISS btclib-node#1190](https://github.com/btclib-org/btclib-node/issues/1190));
`p2p_blockfilters.py` on `-blockfilterindex` and BIP157, neither
adapter's own surface.

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
while keeping a fixed-fee change output cached back to the wallet the
way `create_self_transfer` already does. Both are unit-tested against
the fake RPC alongside the rest of `mini_wallet_test.py`.

`mempool_datacarrier.py`'s own row is a smaller claim than Core's own
file: kept is that the default setting relays a sizeable `OP_RETURN`,
`-datacarrier` disabled refuses one of any size (even a bare, empty
one), a custom `-datacarriersize` bounds the payload at its own
boundary, and `getmempoolinfo` reports bare multisig permitted by
default, the check Core's own file carries for `mempool_dust.py`'s
option. Dropped is Core's own extra node, a further custom
`-datacarriersize` value, and its own sweep of `None`/empty/single-byte
payloads across every node, neither reaching a boundary the kept
configurations do not already cover.

`mempool_dust.py`'s own row is a smaller claim than Core's own file too:
kept is that a value clearly under the dust threshold is refused and one
clearly over it is allowed, for every output shape Core's own list
names that `ScriptPubKey` builds -- P2PK uncompressed and compressed,
P2PKH, P2SH, P2WPKH, P2WSH, P2TR and the largest standard bare multisig
-- and that `-dustrelayfee` disabled waives the check entirely. Dropped
is Core's own file's exact per-byte threshold arithmetic
(`GetDustThreshold`'s own formula), its future-witness-version rows,
`ScriptPubKey` having no generic future-witness-version output of its
own, its null data row, whose threshold is zero and so sits on neither
side of a boundary, its own sweep of several
other `-dustrelayfee` values, and its own ephemeral-dust scenario.
Ephemeral dust is not the dust threshold at a coarser grain but its own
acceptance rule, `src/policy/ephemeral_policy.cpp`'s
`CheckEphemeralSpends`, exempting a dust output its package spends. It
is the subject of Core's own `mempool_ephemeral_dust.py`, not yet ported.

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
reflecting the sigop-adjusted floor.

Every `btclib-node` cell across this trio is a counted skip on its own
option capability alone, ahead of `Capability.MINE` which every row also
needs: measured against `cli.py`'s registered options, `_build_parser`
on the released build and `_OPTIONS` on `main`, none of `-datacarrier`,
`-datacarriersize`, `-permitbaremultisig`, `-dustrelayfee` or
`-bytespersigop` is one of its registered flags, so `require` never
reaches `Capability.MINE` at all.
