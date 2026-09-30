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

Verdict: **tf2's (harness)**. `fill_mempool` is ported, in
`src/bitcoin_node_tests/mempool_util.py`, over a throwaway `MiniWallet`
from `mini_wallet.py`
([ISS bitcoin-node-tests#70](https://github.com/btclib-org/bitcoin-node-tests/issues/70)).
`tx_in_orphanage` is `tests/integration/rpc_orphans_test.py`'s own
`in_orphanage`, and `create_large_orphan` is
`tests/integration/p2p_orphan_handling_test.py`'s own `_large_orphan`;
`assert_mempool_contents` is not ported.

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
`btclib` names SOCKS nowhere; `socks5.py`'s `Socks5Proxy` is this
repository's.

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

A `btclib-node` cell may give a verdict on the build the row was
measured against and others on later builds, where the capability it
names is declared by a probe of the build rather than by the adapter's
class: the row's own paragraph below names the probe and the issue it
tracks.

A `btclib-node` cell reading **fail** carries the same build-qualified
form once the issue it names closes: `fail (...) on the build; pass on
a build past [ISS ...]`, both halves naming the one issue, where a skip
cell's first half names a capability instead.

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
| `feature_blocksdir.py` | `0d1301b47a35` | 2026-03-24 | pass | fail ([ISS btclib-node#1416](https://github.com/btclib-org/btclib-node/issues/1416)) on the build; skip (blk) on a build past [ISS btclib-node#1416](https://github.com/btclib-org/btclib-node/issues/1416) |
| `feature_filelock.py` | `fa5f29774872` | 2025-12-16 | pass | fail ([ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147)) on the build; pass on a build past [ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147) |
| `rpc_whitelist.py` | `fa24693819e0` | 2026-05-26 | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `rpc_users.py` | `faf993ee4421` | 2026-05-26 | pass | skip (rpc_auth) on the build; fail ([ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210)) on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) and before [ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210); pass on a build past [ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210) |
| `rpc_users.py` (`-norpcauth`) | same | same | pass | skip (rpc_auth_negation) on the build; pass on a build past [ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176) |
| `rpc_users.py` (`-rpcuser`/`-rpcpassword`) | same | same | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `rpc_users.py` (`-norpccookiefile`) | same | same | pass | skip (rpc_auth) on the build; pass on a build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070) |
| `p2p_block_sync.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks_hb.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) on the build; skip (disconnect) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_getdata.py` | `aaf941202667` | 2026-07-31 | pass | fail ([ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)) on the build; pass on a build past [ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072) |
| `p2p_invalid_locator.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) on the build; fail ([ISS btclib-node#1385](https://github.com/btclib-org/btclib-node/issues/1385)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_invalid_messages.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_invalid_messages.py` (log) | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `p2p_invalid_messages.py` (inv, wire) | same | same | pass | fail ([ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)) on the build; pass on a build past [ISS btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145) |
| `p2p_invalid_messages.py` (inv, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (getdata, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (getdata, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (headers, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (headers, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (invalid pow, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (invalid pow, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (size, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (size, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (dup version, wire) | same | same | pass | fail ([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)) on the build; pass on a build past [ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133) |
| `p2p_invalid_messages.py` (dup version, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (checksum, wire) | same | same | pass | fail ([ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)) on the build; pass on a build past [ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130) |
| `p2p_invalid_messages.py` (checksum, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (msgtype, wire) | same | same | pass | fail ([ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)) on the build; pass on a build past [ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130) |
| `p2p_invalid_messages.py` (msgtype, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 empty, wire) | same | same | pass | fail ([ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)) on the build; pass on a build past [ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170) |
| `p2p_invalid_messages.py` (addrv2 empty, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 no addr, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 no addr, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 long, wire) | same | same | pass | fail ([ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)) on the build; pass on a build past [ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170) |
| `p2p_invalid_messages.py` (addrv2 long, log) | same | same | pass | skip |
| `p2p_invalid_messages.py` (addrv2 net id, wire) | same | same | pass | pass |
| `p2p_invalid_messages.py` (addrv2 net id, log) | same | same | pass | skip |
| `p2p_leak.py` (wire) | `01b8a117d2c5` | 2026-06-04 | pass | pass |
| `p2p_leak.py` (log) | `01b8a117d2c5` | 2026-06-04 | pass | skip |
| `p2p_handshake.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | fail ([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)) on the build; pass on a build past [ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133) |
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
| `rpc_uptime.py` | `406c2348ddbf` | 2026-06-13 | pass | skip (clock) |
| `feature_torcontrol.py` | `4556ef626754` | 2026-09-15 | pass, the `PoWDefensesEnabled` flag asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `p2p_bip434_feature.py` | `da74ff9ca49e` | 2026-06-04 | pass, `FEATURE`'s own disconnects asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | bitcoind only |
| `feature_framework_miniwallet.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `feature_framework_miniwallet.py` (`confirmed_only`) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (generate) |
| `feature_framework_miniwallet.py` (`fee_rate`) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1397](https://github.com/btclib-org/btclib-node/issues/1397)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `feature_framework_miniwallet.py` (TRUC) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1398](https://github.com/btclib-org/btclib-node/issues/1398)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `mempool_resurrect.py` | `fa5f29774872` | 2025-12-16 | pass | skip (mine) on the build; fail ([ISS btclib-node#1388](https://github.com/btclib-org/btclib-node/issues/1388)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `mempool_spend_coinbase.py` | `6eca11175be6` | 2026-07-16 | pass | skip (mine) on the build; fail ([ISS btclib-node#1328](https://github.com/btclib-org/btclib-node/issues/1328)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `feature_dersig.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_dersig.py` (wire) | same | same | pass | skip |
| `feature_dersig.py` (log) | same | same | pass | skip |
| `feature_dersig.py` (signature) | same | same | pass | skip |
| `feature_cltv.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_cltv.py` (wire) | same | same | pass | skip |
| `feature_cltv.py` (log) | same | same | pass | skip |
| `feature_cltv.py` (failures, activation) | same | same | pass | skip |
| `feature_cltv.py` (failures, mempool) | same | same | pass | skip |
| `feature_cltv.py` (failures, block) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1390](https://github.com/btclib-org/btclib-node/issues/1390)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `feature_csv_activation.py` | `fab352053d6e` | 2026-04-16 | pass | skip |
| `feature_csv_activation.py` (lock times) | same | same | pass | skip |
| `feature_nulldummy.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `feature_dirsymlinks.py` | `fa5f29774872` | 2025-12-16 | pass | pass |
| `feature_posix_fs_permissions.py` | `3fd68a95e68b` | 2026-04-07 | pass | fail ([ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198)) on the build; pass on a build past [ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198) |
| `rpc_createmultisig.py` | `771200ca4362` | 2026-06-30 | pass | bitcoind only |
| `rpc_createmultisig.py` (spend) | same | same | pass, `combinerawtransaction`'s mergeability refusals asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (sign_raw_transaction) |
| `rpc_setban.py` (ban) | `fa21edddb272` | 2026-03-27 | pass | skip (ban) on the build; pass on a build past [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088) |
| `rpc_setban.py` (restart) | same | same | pass | skip (ban) on the build; skip (debug_log) on a build past [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088) |
| `rpc_setban.py` (noban) | same | same | pass | skip (ban) on the build; fail ([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)) on a build past [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088) |
| `rpc_setban.py` (non-IP) | same | same | pass | skip (ban) on the build; fail ([ISS btclib-node#1218](https://github.com/btclib-org/btclib-node/issues/1218)) on a build past [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088) and before [ISS btclib-node#1218](https://github.com/btclib-org/btclib-node/issues/1218); pass on a build past [ISS btclib-node#1218](https://github.com/btclib-org/btclib-node/issues/1218) |
| `rpc_setban.py` (bantime) | same | same | pass | skip (ban) on the build; pass on a build past [ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088) |
| `p2p_disconnect_ban.py` (disconnectnode) | [`dcd90fbe54cf`](https://github.com/bitcoin/bitcoin/commit/dcd90fbe54cf) | 2026-04-07 | pass | skip (disconnect) |
| `mempool_datacarrier.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_dust.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_sigoplimit.py` | `5d25a0c28d19` | 2026-07-07 | pass | skip |
| `mempool_package_limits.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `mempool_updatefromblock.py` | `fa6b05c96ffb` | 2026-03-12 | pass | skip |
| `p2p_leak_tx.py` (in block) | `fa5f29774872` | 2025-12-16 | pass | skip |
| `p2p_leak_tx.py` (replaced) | same | same | pass | skip |
| `p2p_leak_tx.py` (unannounced) | same | same | pass | skip |
| `feature_utxo_set_hash.py` | `58eeab790d98` | 2026-05-13 | pass | skip (mine) on the build; fail ([ISS btclib-node#1387](https://github.com/btclib-org/btclib-node/issues/1387)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `rpc_getdescriptoractivity.py` | `3fd68a95e68b` | 2026-04-07 | pass | skip |
| `rpc_getdescriptoractivity.py` (mempool) | same | same | pass | skip |
| `rpc_getblockstats.py` | `b7cbd804284b` | 2026-05-25 | pass | skip (stats) |
| `feature_fastprune.py` | `fa5f29774872` | 2025-12-16 | pass | skip |
| `rpc_scanblocks.py` | `aeca0610865e` | 2026-07-01 | pass | skip |
| `rpc_scanblocks.py` (no index) | same | same | pass | skip |
| `p2p_eviction.py` | `1b76e0473647` | 2026-07-24 | pass, `-maxconnections` read per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (inbound_eviction) on the build; skip (mine) on a build past [ISS btclib-node#1064](https://github.com/btclib-org/btclib-node/issues/1064) and before [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071); fail ([ISS btclib-node#1179](https://github.com/btclib-org/btclib-node/issues/1179)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) and before [ISS btclib-node#1179](https://github.com/btclib-org/btclib-node/issues/1179); pass on a build past [ISS btclib-node#1179](https://github.com/btclib-org/btclib-node/issues/1179) |
| `feature_presegwit_node_upgrade.py` | [`fad7bd9ba3ee`](https://github.com/bitcoin/bitcoin/commit/fad7bd9ba3ee) | 2026-01-14 | pass | skip (test_activation_height) |
| `rpc_validateaddress.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (validate_address) |
| `p2p_addrfetch.py` | [`3fd68a95e68b`](https://github.com/bitcoin/bitcoin/commit/3fd68a95e68b) | 2026-04-07 | pass | skip (typed_outbound) |
| `rpc_echo_payload.py` | [`fa7bc26d1276`](https://github.com/bitcoin/bitcoin/commit/fa7bc26d1276) | 2026-08-06 | pass | skip (rpc_work_queue) |
| `p2p_compactblocks_blocksonly.py` | [`bf9884f4e55d`](https://github.com/bitcoin/bitcoin/commit/bf9884f4e55d) | 2026-06-18 | pass, the ignored `cmpctblock` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (blocks_only) |
| `rpc_getblockfilter.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (block_filter_index) |
| `rpc_getblockfrompeer.py` | [`779f4446803d`](https://github.com/bitcoin/bitcoin/commit/779f4446803d) | 2026-05-25 | pass | skip (block_from_peer) |
| `p2p_node_network_limited.py` | [`fa7bac94d87a`](https://github.com/bitcoin/bitcoin/commit/fa7bac94d87a) | 2026-03-12 | pass | skip (mine) on the build; skip (disconnect) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `rpc_getdescriptorinfo.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (descriptor_info) |
| `p2p_timeouts.py` (wire) | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (peer_timeout) |
| `p2p_timeouts.py` (log) | same | same | pass | skip (peer_timeout) |
| `p2p_timeouts.py` (refusal) | same | same | pass | skip (peer_timeout) |
| `p2p_ping.py` (wire) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (peer_timeout) |
| `p2p_ping.py` (log) | same | same | pass | skip (peer_timeout) |
| `mempool_expiry.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (mempool_expiry) |
| `p2p_add_connections.py` | [`4c79f3a34d00`](https://github.com/bitcoin/bitcoin/commit/4c79f3a34d00) | 2026-09-14 | pass | skip (typed_outbound) |
| `p2p_add_connections.py` (`manual`) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `feature_includeconf.py` (order) | [`fa71c15f8610`](https://github.com/bitcoin/bitcoin/commit/fa71c15f8610) | 2025-11-26 | pass | skip (ua_comment) |
| `feature_includeconf.py` (double negative) | same | same | pass | fail ([ISS btclib-node#1116](https://github.com/btclib-org/btclib-node/issues/1116)) on the build; fail ([ISS btclib-node#1402](https://github.com/btclib-org/btclib-node/issues/1402)) on a build past [ISS btclib-node#1409](https://github.com/btclib-org/btclib-node/issues/1409) and before [ISS btclib-node#1402](https://github.com/btclib-org/btclib-node/issues/1402); pass on a build past [ISS btclib-node#1402](https://github.com/btclib-org/btclib-node/issues/1402) |
| `feature_includeconf.py` (`-includeconf`) | same | same | pass | fail ([ISS btclib-node#1116](https://github.com/btclib-org/btclib-node/issues/1116)) on the build; pass on a build past [ISS btclib-node#1409](https://github.com/btclib-org/btclib-node/issues/1409) |
| `feature_includeconf.py` (nested) | same | same | pass | fail ([ISS btclib-node#1403](https://github.com/btclib-org/btclib-node/issues/1403)) on the build; pass on a build past [ISS btclib-node#1403](https://github.com/btclib-org/btclib-node/issues/1403) |
| `feature_includeconf.py` (missing) | same | same | pass | fail ([ISS btclib-node#1187](https://github.com/btclib-org/btclib-node/issues/1187)) on the build; pass on a build past [ISS btclib-node#1187](https://github.com/btclib-org/btclib-node/issues/1187) |
| `feature_reindex_init.py` | [`0d1301b47a35`](https://github.com/bitcoin/bitcoin/commit/0d1301b47a35) | 2026-03-24 | pass | skip (reindex_after_failure) |
| `rpc_generate.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (generate) |
| `rpc_signrawtransactionwithkey.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (sign_raw_transaction) |
| `rpc_scantxoutset.py` | [`b388674acf06`](https://github.com/bitcoin/bitcoin/commit/b388674acf06) | 2026-08-06 | pass, `start`'s refusal of a null scan-object list asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (scan_utxo_set) |
| `feature_proxy.py` | [`f82043af507a`](https://github.com/bitcoin/bitcoin/commit/f82043af507a) | 2026-06-30 | pass | skip (proxy) |
| `feature_proxy.py` (`-cjdnsreachable`) | same | same | pass | skip (cjdns) |
| `feature_proxy.py` (`-i2psam`) | same | same | pass | skip (i2p_sam) |
| `feature_proxy.py` (`-onlynet`) | same | same | pass | skip (onlynet) |
| `wallet_signmessagewithaddress.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_blank.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `wallet_coinbase_category.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (node_wallet) |
| `p2p_initial_headers_sync.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | fail ([ISS btclib-node#1073](https://github.com/btclib-org/btclib-node/issues/1073)) on the build; fail ([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410)) on a build past [ISS btclib-node#1073](https://github.com/btclib-org/btclib-node/issues/1073) |
| `p2p_initial_headers_sync.py` (stall, wire) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (stall, log) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (noban, wire) | same | same | pass | skip |
| `p2p_initial_headers_sync.py` (noban, log) | same | same | pass | skip |
| `p2p_sendtxrcncl.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (tx_reconciliation) |
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
| `feature_reindex.py` (interrupted) | same | same | pass | skip (reindex) |
| `feature_reindex_readonly.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (reindex) |
| `p2p_feefilter.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | pass |
| `p2p_feefilter.py` (forcerelay) | same | same | pass | fail ([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)) |
| `p2p_feefilter.py` (filter) | same | same | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_feefilter.py` (block-relay-only) | same | same | pass | skip |
| `p2p_feefilter.py` (blocksonly) | same | same | pass | skip |
| `p2p_mutated_blocks.py` (wire) | [`9c5dd2926aa9`](https://github.com/bitcoin/bitcoin/commit/9c5dd2926aa9) | 2026-06-18 | pass | skip |
| `p2p_mutated_blocks.py` (log) | same | same | pass | skip |
| `p2p_mutated_blocks.py` (missing parent, wire) | same | same | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_mutated_blocks.py` (missing parent, log) | same | same | pass | skip |
| `feature_anchors.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (typed_outbound) |
| `feature_anchors.py` (onion) | same | same | pass | skip (typed_outbound) |
| `p2p_addr_selfannouncement.py` (inbound, wire) | [`dab7f2c984bd`](https://github.com/bitcoin/bitcoin/commit/dab7f2c984bd) | 2026-07-07 | pass | skip |
| `p2p_addr_selfannouncement.py` (inbound, log) | same | same | pass | skip |
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
| `mempool_accept_wtxid.py` | [`3f5211cba8e7`](https://github.com/bitcoin/bitcoin/commit/3f5211cba8e7) | 2026-01-21 | pass | skip (mine) on the build; fail ([ISS btclib-node#1397](https://github.com/btclib-org/btclib-node/issues/1397)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `rpc_orphans.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (orphanage) |
| `mining_template_verification.py` | [`6eca11175be6`](https://github.com/bitcoin/bitcoin/commit/6eca11175be6) | 2026-07-16 | pass | skip (block_proposal) |
| `p2p_i2p_ports.py` | [`fa20275db32c`](https://github.com/bitcoin/bitcoin/commit/fa20275db32c) | 2025-10-21 | pass | skip (i2p_sam) |
| `p2p_i2p_sessions.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (i2p_sam) |
| `p2p_dns_seeds.py` | [`fa4cb96bdec2`](https://github.com/bitcoin/bitcoin/commit/fa4cb96bdec2) | 2026-02-17 | pass | skip (dns_seed) |
| `p2p_seednode.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (address_fetch) |
| `p2p_ibd_stalling.py` (wire) | [`24628d3ae7dc`](https://github.com/bitcoin/bitcoin/commit/24628d3ae7dc) | 2026-09-14 | pass | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (log) | same | same | pass | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (`manual`, wire) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_ibd_stalling.py` (`manual`, log) | same | same | pass, `manual` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_private_broadcast.py` | [`ac6b6c1f06e9`](https://github.com/bitcoin/bitcoin/commit/ac6b6c1f06e9) | 2026-08-18 | pass, the refusals without `-privatebroadcast` and `attempts_remaining` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (private_broadcast) |
| `p2p_tx_download.py` (expiry) | [`1278a5970d5a`](https://github.com/bitcoin/bitcoin/commit/1278a5970d5a) | 2026-08-06 | pass | skip (clock) |
| `p2p_tx_download.py` (disconnect) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1196](https://github.com/btclib-org/btclib-node/issues/1196)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_tx_download.py` (notfound) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1196](https://github.com/btclib-org/btclib-node/issues/1196)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_tx_download.py` (tiebreak) | same | same | pass | skip (typed_outbound) |
| `p2p_tx_download.py` (inbound) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (outbound) | same | same | pass | skip (typed_outbound) |
| `p2p_tx_download.py` (noban) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (txid) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (txid beside wtxid) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (large inv) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_tx_download.py` (duplicate inv) | same | same | pass, the duplicates asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (debug_log) |
| `p2p_tx_download.py` (spurious notfound) | same | same | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_tx_download.py` (in flight) | same | same | pass | skip (clock) |
| `p2p_tx_download.py` (inv block) | same | same | pass | skip (clock) |
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
| `p2p_compactblocks.py` (sendcmpct) | [`28641fd195db`](https://github.com/bitcoin/bitcoin/commit/28641fd195db) | 2026-07-31 | pass | skip (mine) on the build; fail ([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (construction) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (requests) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (getblocktxn requests) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (getblocktxn handler) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (not at tip) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (low work, wire) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1393](https://github.com/btclib-org/btclib-node/issues/1393)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (low work, log) | same | same | pass | skip |
| `p2p_compactblocks.py` (incorrect blocktxn) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (end to end) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (invalid tx) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (empty getblocktxn, wire) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | fail ([ISS btclib-node#1450](https://github.com/btclib-org/btclib-node/issues/1450)) |
| `p2p_compactblocks.py` (empty getblocktxn, log) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_compactblocks.py` (multiple blocktxn, wire) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (multiple blocktxn, log) | same | same | pass | skip |
| `p2p_compactblocks.py` (invalid sendcmpct, wire) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | fail ([ISS btclib-node#1451](https://github.com/btclib-org/btclib-node/issues/1451)) |
| `p2p_compactblocks.py` (invalid sendcmpct, log) | same | same | pass, the disconnect asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip |
| `p2p_compactblocks.py` (invalid cmpctblock) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (sendcmpct, outbound) | same | same | pass | skip |
| `p2p_compactblocks.py` (stalling peer) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (parallel reconstruction) | same | same | pass | skip |
| `p2p_compactblocks.py` (high-bandwidth states) | same | same | pass | skip (mine) on the build; fail ([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_compactblocks.py` (ignored) | same | same | pass, the ignored `cmpctblock` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (mine) on the build; fail ([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321)) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `feature_startupnotify.py` | [`fa71c15f8610`](https://github.com/bitcoin/bitcoin/commit/fa71c15f8610) | 2025-11-26 | pass | skip (startup_notify) |
| `rpc_dumptxoutset.py` | [`58eeab790d98`](https://github.com/bitcoin/bitcoin/commit/58eeab790d98) | 2026-05-13 | pass, the dump at a forked height asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (dump_utxo_set) |
| `feature_loadblock.py` | [`fa4fc8c1d7b5`](https://github.com/bitcoin/bitcoin/commit/fa4fc8c1d7b5) | 2026-05-22 | pass | skip (load_block) |
| `feature_port.py` | [`997757dd2b4d`](https://github.com/bitcoin/bitcoin/commit/997757dd2b4d) | 2024-11-15 | pass | skip (listen_address) |
| `p2p_opportunistic_1p1c.py` (parent first) | [`0bd3d3dfa562`](https://github.com/bitcoin/bitcoin/commit/0bd3d3dfa562) | 2026-07-24 | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent first, P2PK) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (child first) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (low, high child) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (low, high, P2PK) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (orphan invalid) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent invalid) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (multiple parents) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (parent in mempool) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (1p1c on 1p1c) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (DoS, large orphans) | same | same | pass | skip |
| `p2p_opportunistic_1p1c.py` (DoS, many orphans) | same | same | pass | skip |
| `p2p_block_times.py` | [`5d5397d84108`](https://github.com/bitcoin/bitcoin/commit/5d5397d84108) | 2026-07-25 | pass, `last_block_announcement` asserted per-build ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)) | skip (typed_outbound) |
| `p2p_outbound_eviction.py` (unprotected) | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip |
| `p2p_outbound_eviction.py` (protected) | same | same | pass | skip |
| `p2p_outbound_eviction.py` (mixed) | same | same | pass | skip |
| `p2p_outbound_eviction.py` (block-relay-only) | same | same | pass | skip |
| `p2p_tx_privacy.py` | [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) | 2025-12-16 | pass | skip (mine) on the build; pass on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_invalid_block.py` (wire) | [`fa16bc53d79c`](https://github.com/bitcoin/bitcoin/commit/fa16bc53d79c) | 2026-04-16 | pass | skip (mine) on the build; skip (clock) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |
| `p2p_invalid_block.py` (log) | same | same | pass | skip (mine) on the build; skip (clock) on a build past [ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071) |

`feature_blocksdir.py`'s row is a smaller claim than Core's own test:
Core also mines blocks through the framework's own deterministic wallet
key before its disk read, which this drops -- a fresh node writes its
genesis block to `blk00000.dat` before anything is mined, so the
`-blocksdir` redirect this test is about needs nothing more than that
to show. On a btclib-node build past
[ISS btclib-node#1416](https://github.com/btclib-org/btclib-node/issues/1416)
the cell names the capability rather than the node's whole behaviour: a
nonexistent `-blocksdir` is fatal there too, in bitcoind's own words,
and it is reading the chain back in Core's own `blk*.dat` layout that is
`Capability.BLK_FILES` (`capability.py`) -- a capability btclib-node
never declares, not a gap its adapter is waiting on but the decision
[ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)
already closed on.

The refusal itself is matched as the node's whole stderr, the path
given included, the way Core's own file compares it, and in Core's own
wording alone: `Error: Specified blocks directory "..." does not
exist.`. The released btclib-node writes its own `btclib-node: specified
blocks directory ... does not exist`, lower-cased and without the quotes
or the trailing period, and fails the row on that wording.
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
a blocksdir, a first one already holds is fatal, matched in Core's own
wording alone, "Cannot obtain a lock on directory ...", the locked
directory's path included. btclib-node writes it past
[ISS btclib-node#1147](https://github.com/btclib-org/btclib-node/issues/1147),
locking the data directory and then the blocks directory before either
store opens. The released build fails the row: its chainstate and
blocks databases -- each its own `Rdict` (RocksDB) -- fail uncaught,
measured live as `Exception: IO error: While lock file: .../LOCK:
Resource temporarily unavailable`.

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
`skip (rpc_auth)` on the build with `rpc_whitelist.py`'s own row above,
and is a smaller claim than Core's own file in the same way. Kept: `-rpcauth`
authenticating a user given either through `bitcoin.conf` or on the
command line, a wrong password or a wrong user refused where a correct
one is accepted; `test_rpccookieperms`'s own POSIX permission bits
(`-rpccookieperms=owner`/`group`/`all`, and the default with none
given); a roster of Core's own malformed `-rpcauth` values, refused at
startup and matched against Core's own wording; Core's own
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
`rpc_users.py` row's `RPC_AUTH_CONFIG` cell: a `btclib-node` build can
read `-rpcauth` and still refuse `-norpcauth` before a node ever starts,
which `btclib_node.py`'s own module docstring measures.
`BitcoindAdapter` declares the new capability unconditionally, the same
way it declares `RPC_AUTH_CONFIG`; `BtclibNodeAdapter` declares it per
instance, where its own `_negates_rpcauth` probe finds the build's
`cli.build_config` discarding an `-rpcauth` given before `-norpcauth`
([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)).
The released build's argparse refuses `-norpcauth` as "unrecognized
arguments", so the `-norpcauth` row's `btclib-node` cell is a counted
skip on the build and a run on `main`.

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

A cookie write failure happens inside `Node.run` on btclib-node, once
`rpc_manager.start_listener` has already tried and failed, and
`__init__.py`'s own `RPC_INIT_ERROR` constant is bitcoind's own generic
wording verbatim -- measured live, a directory sitting where the cookie
file must go refuses with `Error: Unable to start HTTP server. See debug
log for details.` on both nodes, identically. A malformed `-rpcauth`
answers with that same wording on btclib-node's `main`, past
[ISS btclib-node#1210](https://github.com/btclib-org/btclib-node/issues/1210):
`RpcAuth.start` logs "Invalid -rpcauth argument." and fails the
listener, as Core's own `InitRPCAuthentication` refuses it once bound.
A build past [ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
and before that issue writes "Error: Invalid -rpcauth argument."
instead, `rpc/auth.py`'s own `RpcAuthEntry.parse` raising out of
`config.py`'s own `Config`, and fails the row: btclib-node's test
matches Core's wording alone.

`p2p_getdata.py`'s row is a smaller claim than Core's own test: Core
asks its "later valid `getdata`" question of a mined tip, and this asks
it of genesis instead, `Capability.MINE` not being every node's fact
yet. The invalid-`getdata`-then-`ping` half is unchanged from Core's.
Step 4 ([ISS bitcoin-node-tests#2](https://github.com/btclib-org/bitcoin-node-tests/issues/2))
re-asked whether that claim should widen now that `Capability.MINE`
exists: it does not, because `BtclibNodeAdapter` declares
`Capability.MINE` only on a build that connects a submitted block with
no peer -- `main` from the commit closing
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
on, and not the released build -- and widening only the bitcoind half
of this row would leave its own column and btclib-node's answering a
different question about the same test.

The first family's own rows -- `p2p_block_sync.py`,
`p2p_compactblocks_hb.py`, `p2p_invalid_locator.py` and
`p2p_net_deadlock.py` -- are Core's own claim in full, `bitcoind`'s pass
being the whole of it: none narrows what Core asks, each needing
`Capability.MINE` (`p2p_block_sync.py`, `p2p_compactblocks_hb.py` and
`p2p_invalid_locator.py`, to reach a chain tall enough to mine or to
name, and `Capability.DISCONNECT` besides for `p2p_compactblocks_hb.py`)
or `Capability.RAW_MESSAGE` (`p2p_net_deadlock.py`, Core's own
`sendmsgtopeer`), so every `btclib-node` cell is a counted skip rather
than a run on the released build, which declares none of them -- naming the
capability rather than the RPC, since a node offering the same fact
under another name would still answer `pass`. Every row of these is one
body run against both nodes
(`tests/integration/conftest.py`'s own module docstring), so a `main`
declaring `Capability.MINE` (`btclib_node.py`'s own docstring) runs
Core's own scenario: `p2p_block_sync.py` passes; `p2p_compactblocks_hb.py`
skips on `Capability.DISCONNECT` instead, each relay dropping its link to
the block producer over `disconnectnode`; and `p2p_invalid_locator.py`
fails its `getblocks` half, a message that build leaves unanswered
([ISS btclib-node#1385](https://github.com/btclib-org/btclib-node/issues/1385)).
`p2p_net_deadlock.py` skips on `Capability.RAW_MESSAGE`, which it asks for
ahead of `Capability.MINE`.
`p2p_compactblocks_hb.py` identifies each of the node under test's own
peers by connection order rather than by the `-uacomment` Core's own
`TestNode` sets, this adapter carrying no per-node command-line option;
every other assertion is unchanged.

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
about. `tests/integration/p2p_invalid_messages_misbehaving_test.py`'s
own docstring has the full argument, including why the PoW check needs
none of Core's own preliminary "send a valid header first" step. Of
these, only the oversized-`inv` row disagrees on btclib-node's own
released build: its own `p2p.callbacks.inv` returns before `Inv.parse`
ever runs while the node has not reached `NodeStatus.BlockSynced`, a
status this adapter's own peerless node never advances past, so an
oversized announcement is dropped unread rather than refused
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
`tests/integration/p2p_invalid_messages_test.py`'s own docstring
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
`tests/integration/p2p_invalid_messages_dropped_test.py`'s own
docstring has the full argument, including why Core's own
`bytesrecv_per_msg` check on the checksum and msgtype rows is dropped.
Every one of them disagrees on btclib-node's own released build, and by
a single shared mechanism rather than a distinct one each:
`Connection.run`'s own handler around `frame_message` (`connection.py`)
discourages and stops on *any* `BTClibException`, where Core only logs
and drops the one message --
`btclib.p2p.message._command_from_bytes` raises the identical exception
class for an invalid command that `Message.parse`'s own checksum check
does, so the checksum and msgtype rows are the same defect measured
again. [ISS btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130)
names it. The duplicate-version row fails on that build for a
different, adjacent reason: `handle_p2p_handshake`'s own dispatch
(`p2p/main.py`) discourages
and stops a `version`/`verack`/`wtxidrelay`/`sendaddrv2` arriving once the
connection is already `Connected`, ahead of the `version` callback's own
guard against a *pre-verack* repeat.
[ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)
names it.

Core's own `test_addrv2_*` checks join the same shape, through a
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
btclib-node's own released build, by a distinct but adjacent mechanism:
`btclib_node.p2p.callbacks.addrv2` calls `AddrV2.parse` with no
`try`/`except` of its own, and `handle_p2p`'s own `_drop` (`p2p/main.py`)
discourages and stops the connection for any `BTClibException` a
callback raises -- the dispatch-level path
[ISS btclib-node#1170](https://github.com/btclib-org/btclib-node/issues/1170)
names, rather than the checksum and msgtype rows' own frame-level one.
`test_addrv2_no_addresses` raises nothing -- an empty list is valid --
so it passes on both nodes.

`test_addrv2_unrecognized_network` joins them. Its assertion lines
past Core's first are `LogDebug(BCLog::ADDRMAN, ...)`'s (`src/addrman.cpp`),
and `BitcoindAdapter._command` enables that category beside `net`,
`-debug` accumulating rather than one occurrence replacing another. Its
node is started for the test, with the address-relay permission and the
disabled autoconnect Core's own run of the file has and the session's
shared node does not:
`tests/integration/p2p_invalid_messages_addrv2_bitcoind_test.py`'s own
docstring has why each is needed, including the `addrman` lines a node
holding the gossiped address writes without the second, measured
against the pinned release. It passes on both nodes: `AddrV2.parse`
reads an entry of a network id BIP155 does not name the way it reads any
other, so btclib-node raises nothing either.

`p2p_bip434_feature.py`'s row is ported, narrowed to what a build lacking
BIP434 support disconnects for anyway rather than to `FEATURE`'s own
accepted shapes -- the length-boundary and acceptance checks Core's own
file also carries read the log of a node that file starts with
`-peertimeout` above its default, so they are
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
rather than this row's, and this row passes no `-peertimeout` -- and
gated on a fact read
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
fails the required job on any skip whose reason does not start with
its `skip-reason-prefix`, which `node-integration.yml`'s `bitcoind` job
sets to the start of `btclib_node_python`'s own skip message. `doc/bips.md` at
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

`p2p_handshake.py`, `p2p_addr_relay.py` and `p2p_addrv2_relay.py` give
the log family more checks of the same wire-and-log shape (issue #5),
each the first check of its own file's `run_test`: a second `verack` once
the handshake is complete, ignored; an `addr` over `MAX_ADDR_TO_SEND`, a
`Misbehaving` line and a disconnect; and a `sendaddrv2` after `verack`, a
disconnect. Each is one body over both nodes
(`tests/integration/conftest.py`'s own module docstring), whose own
module docstring has what of Core's file it drops. The redundant-`verack`
row's wire half disagrees on btclib-node's released build for the reason
the duplicate-`version` row's does
([ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)).

The log family's census is Core's `test/functional/` at `master`
`ed7dd7cf4e`, every file this command lists:

```shell
git -C ../bitcoin grep -l -E \
    'assert_debug_log|debug_log|debug\.log|reject_reason=|clear_addrman=True' \
    ed7dd7cf4e -- 'test/functional/*.py' ':!test/functional/test_framework/*'
```

`reject_reason=` and `clear_addrman=True` in the pattern are the
framework's own calls to `assert_debug_log`, which a grep for the name
alone does not find:
`P2PDataStore`'s `send_blocks_and_test` and `send_txs_and_test`
(`test_framework/p2p.py`) make one for a caller passing `reject_reason`,
and `restart_node` (`test_framework/test_framework.py`) one for a caller
passing `clear_addrman=True`. Each file is read at the grain Core's own file
gives it, a `test_*` method or a `self.log.info` step of `run_test`, and a
step asks for the log alone only where it reaches no option, no
`MiniWallet` coin, no `setmocktime`, no read of the node's own files and
no second node linked to its own, counting whatever an earlier step or the
file's own setup already gave the same node. Core's `setup_network` links
every node of a file starting more than one, unless the file overrides
it, and its `generate` then syncs them. Not counted: a permission the
step's own check never reads, the narrowing the `p2p_invalid_messages.py`
rows above already make, and an option set to its own default.

Open under
[ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5), each a
step of that shape and none ported yet:

- `p2p_invalid_messages.py`'s `test_noncontinuous_headers_msg`, which
  also needs `Capability.MINE`, an adapter's own fact rather than a step-5
  mechanism;
- `feature_assumevalid.py`'s first node, started without `-assumevalid`
  and fed a chain whose invalid signature it refuses, every other node of
  the file being given the option;
- `p2p_nobloomfilter_messages.py`'s filtered-block request, the
  `-peerbloomfilters` value its node is given restating Core's own
  default, and
  `interface_http.py`'s `check_excessive_request_size`: steps Core's
  `master` carries and the pinned release does not.

[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s,
every log step of each reaching another of the mechanisms above:
`feature_abortnode.py`, `feature_addrman.py`, `feature_asmap.py`, the rest
of `feature_assumevalid.py`, `feature_block.py`, `feature_config_args.py`,
`feature_fee_estimation.py`, `feature_index_prune.py`, `feature_init.py`,
`feature_logging.py`, `feature_maxuploadtarget.py`, `feature_port.py`,
`feature_pruning.py`, `feature_reindex.py`, `feature_reindex_readonly.py`,
`feature_settings.py`, `feature_signet.py`,
`feature_utxo_abort_on_error.py`, the rest of `interface_http.py`,
`mempool_limit.py`, `mempool_unbroadcast.py`,
`mining_getblocktemplate_longpoll.py`, the rest of `p2p_addr_relay.py` and
of `p2p_addrv2_relay.py`, the rest of `p2p_bip434_feature.py`,
`p2p_blockfilters.py`, `p2p_compactblocks.py`,
`p2p_connection_limits.py`,
`p2p_disconnect_ban.py`'s `setban` half, `p2p_filter.py`,
`p2p_headers_sync_with_minchainwork.py`, `p2p_ibd_txrelay.py`,
`p2p_invalid_block.py`, `p2p_invalid_tx.py`,
`p2p_permissions.py`,
`p2p_segwit.py`,
`p2p_unrequested_blocks.py`, `p2p_v2_misbehaving.py`,
`p2p_v2_transport.py`, `rpc_misc.py` and `rpc_net.py`. Of these,
`p2p_addr_relay.py` and `p2p_compactblocks.py` also dial out of the node
under test in some step,
[ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44)'s
subject. `rpc_misc.py`'s log check, the `libevent` category's
deprecation warning, is a step of Core's `master` alone, run after its
node restarts with `-txindex` and the other indexes; the file's other
`logging` checks read the RPC's own answer and no log.
`feature_assumeutxo.py` stays behind the disqualifier the node-linking
section below names. `feature_reindex.py`, `feature_reindex_readonly.py`,
`p2p_compactblocks.py` and `p2p_invalid_block.py` are ported, their rows
in the table above.

The rest go where the node wallet, another Core binary, an older release,
a proxy or an external interface is the subject:
[ISS 45](https://github.com/btclib-org/bitcoin-node-tests/issues/45)
every `wallet_*.py` file the command lists,
[ISS 46](https://github.com/btclib-org/bitcoin-node-tests/issues/46)
`feature_coinstatsindex_compatibility.py` and
`feature_txindex_compatibility.py`,
[ISS 48](https://github.com/btclib-org/bitcoin-node-tests/issues/48)
`interface_ipc.py`, and
[ISS 49](https://github.com/btclib-org/bitcoin-node-tests/issues/49)
`interface_bitcoin_cli.py`.

Ledgered already, a row above or a paragraph naming the file:
`p2p_invalid_messages.py` but for the step still open, `p2p_leak.py`,
`rpc_setban.py`, `rpc_users.py`, `feature_posix_fs_permissions.py`,
`feature_cltv.py`, `feature_dersig.py`, `feature_csv_activation.py`,
`p2p_ping.py`, `p2p_timeouts.py`,
`p2p_disconnect_ban.py`'s `disconnectnode` half,
`p2p_bip434_feature.py`'s wire-only disconnects, `p2p_handshake.py`,
`p2p_initial_headers_sync.py`, `p2p_sendtxrcncl.py`,
`p2p_mutated_blocks.py`, `p2p_i2p_ports.py`, `p2p_i2p_sessions.py`,
`p2p_dns_seeds.py`, `feature_anchors.py`,
`p2p_addr_selfannouncement.py`, `p2p_seednode.py`, `p2p_ibd_stalling.py`,
`p2p_private_broadcast.py`, `p2p_tx_download.py`, `p2p_blocksonly.py` and
`p2p_orphan_handling.py`.
Listed and not the family's: `combine_logs.py`,
a tool merging a run's logs that Core's own `test_runner.py` names among
its `NON_SCRIPTS`; and
`interface_rpc.py`, which compares `getrpcinfo`'s `logpath` with a path
and reads no log line.

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
`-uacomment` is not one of `cli.py`'s registered flags, on the released build
or on `main` (`btclib_node.py`'s own docstring has the measurement), so this
row's `btclib-node` cell is a counted skip.

No test measured for this family asks for an option `btclib-node` does register
and needs nothing else from step 5, `MINE` or an outbound connection.
`p2p_add_connections.py` is the one dedicated `-maxconnections` test. Its
options are a loopback `-bind` on some of its nodes, and on another a
`-maxconnections` low enough, with `-listen` off, that its first step fills
that node's outbound capacity before adding a manual connection beyond it.
Every outbound connection it opens has a node dial a listening test peer as a
chosen connection type -- Core's own `add_outbound_p2p_connection`, over
`addconnection` -- beside inbound test peers of its own, and no step links one
node to another. That mechanism is `Capability.TYPED_OUTBOUND` and
`peer.Listener`, save the `manual` type its first step asks for, which
`addconnection` takes only past the pinned release
(bitcoin/bitcoin@4c79f3a34d003bd97824b032383ac816a4147d68).
Its subject is that mechanism (Core's own docstring: "Test
add_outbound_p2p_connection test framework functionality") rather than an
option, so its rows are with the tests the mechanism blocks
([ISS 44](https://github.com/btclib-org/bitcoin-node-tests/issues/44)), not with
this family. `cli.py`'s own `_build_parser` on the released build has no
`-maxconnections` flag either; only `_OPTIONS` on `main` does.
`feature_discover.py`'s own `-discover` is neutered by this adapter's own fixed
`-bind` -- measured against the pinned bitcoind binary, `getnetworkinfo`'s
`localaddresses` answers empty whether `-discover` is passed bare or given its
own disabling value, so
the option has nothing to demonstrate under either adapter's own command line.
So this row exercises the skip arm alone. The pass-through arm's candidates
ask for adapter capabilities besides: `rpc_getblockfrompeer.py`'s and
`p2p_node_network_limited.py`'s rows pass `-prune`, which `cli.py` registers on
both builds, with no capability of its own, and each row's `btclib-node` cell
skips on a capability the node does not declare rather than on the option.

Most of the option family's remaining tests ask for another step-5
mechanism alongside an option -- MiniWallet, `assert_debug_log`,
`setmocktime` or the disk -- and are ISS 14's to port once every family
lands, not this issue's. Of the rest, most name a wallet feature or an
option only bitcoind has a reason to carry (`-torcontrol`), which the
charter's own rule keeps out of this mechanism entirely.
`btclib-node`'s own registered surface carries no
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
and is ISS 14's rather than this one's, its row in the table above.

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
example, is a wallet feature by name and stays out on that ground alone,
and `-proxy` is not bitcoind's alone, `Capability.PROXY` naming it
(*Proxies: `Socks5Proxy`* below).

`p2p_compactblocks_blocksonly.py`'s row is an option-family row, found
by re-running the family's census against Core's own tip rather than
`cff00c5`: `-blocksonly` is `Capability.BLOCKS_ONLY` (`capability.py`),
and every other fact the test asks for -- `Capability.MINE`,
`Capability.CONNECT`, `Capability.DISCONNECT` and a `Peer` (`peer.py`)
-- is the adapters' own rather than another step 5 mechanism. Core
delivers each block itself, over a connection it controls, so the peer
whose `sendcmpct` renegotiation is under test is fixed rather than
raced for one of several slots, and the test reads the wire rather than
`getpeerinfo`: BIP152's `sendcmpct` and `cmpctblock` are
`btclib.p2p.compact_blocks`' own, and `Peer.last_message` is what the
test reads the node's latest `sendcmpct` and `getdata` off. Core's own
claim in full, reached another way at the start: Core's nodes begin on
its cached chain, out of initial block download, and here one block
mined and submitted to every node takes each out of it. That a
`-blocksonly` node ignores a `cmpctblock` is Core's since
bitcoin/bitcoin@bf9884f4e55df502b67b2636969cacce62edaee9, which the
release candidates of the next major release carry and the pinned
release does not: that one reconstructs the block instead, so the test
reads `getnetworkinfo`'s `version` and asserts whichever the build does ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)),
measured against the pinned release and against `v32.0rc2`.
`btclib-node`'s cell is a counted skip: `cli.py` registers no
`-blocksonly`, on the released build or on `main` (`btclib_node.py`'s
own docstring).

`rpc_echo_payload.py`'s row is an option-family row
([ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)).
Its subject is an RPC server's own, not bitcoind's alone: a payload of
any size is either answered or refused, never left to time out, with
`-rpcworkqueue` and `-rpcthreads` set low only so that concurrent
callers fill the queue. Another node's RPC server could make the same
promise, so the pair is `Capability.RPC_WORK_QUEUE` (`capability.py`)
rather than a bitcoind-only row. A smaller claim than Core's own file:
bitcoind's refusal is matched on its HTTP status alone,
`bitcoin_core_rpc`'s own `HttpError` keeping the status and not the
`Work queue depth exceeded` sent with it
(`tests/integration/rpc_echo_payload_test.py`'s own docstring).
`btclib-node`'s cell is a counted skip on that capability: `cli.py`
registers neither option, on the released build or on `main`
(`btclib_node.py`'s own docstring has the measurement). Core's test
sends each payload through `echo` or through `sendrawtransaction`,
chosen at random, and `btclib-node`'s `rpc/callbacks.py` has the second
and not the first, so a port for that node also needs `echo`, and
accepts a refusal in that node's own terms.

`rpc_getblockfilter.py`'s row is an option-family row, Core's own
claim in full: `getblockfilter` answers a filter for every block of an
active chain and of a stale one on a node under `-blockfilterindex`
(`Capability.BLOCK_FILTER_INDEX`), refuses an unknown block and an
unknown filter type, and refuses every filter type once restarted
without the index. Core's harness connects its nodes at setup and its
test disconnects them first; this harness's nodes start unconnected.
`btclib-node`'s cell is a counted skip: `cli.py` registers no
`-blockfilterindex`, and `getblockfilter` names no callback in
`rpc/callbacks.py`'s own dispatch table, on the released build or on
`main`.

`rpc_getblockfrompeer.py`'s row is an option-family row, a smaller claim
than Core's own file in its literals alone:
`tests/integration/rpc_getblockfrompeer_test.py`'s own docstring has
them. Core's cached chain is mined here and submitted to every node, so
the fetched block's hash is the chain's own rather than Core's literal;
and Core's `pruneblockchain` heights are literals that differ between
the pinned release and the pin, so the test asserts what both sets
share instead. `getblockfrompeer` is `Capability.BLOCK_FROM_PEER`,
`-fastprune` `Capability.FASTPRUNE`, and the pre-segwit peer a `Peer`
whose `handshake` offers no `NODE_WITNESS`. `-prune` asks for no
capability, `cli.py` registering it and `rpc/callbacks.py` answering
`pruneblockchain` on the released build and on `main` alike.
`btclib-node`'s cell is a counted skip on `Capability.BLOCK_FROM_PEER`,
asked for first: `getblockfrompeer` names no callback in that dispatch
table on either build.

`p2p_node_network_limited.py`'s row is an option-family row, Core's own
claim in full
([ISS 185](https://github.com/btclib-org/bitcoin-node-tests/issues/185)):
a node under `-prune` signals `NODE_NETWORK_LIMITED` and not
`NODE_NETWORK`, serves a `getdata` for a block near its tip and
disconnects a peer asking for an older one, and a full node syncs from it
only once out of initial block download, asking it for no block outside
that window. `-prune` asks for no capability, as on
`rpc_getblockfrompeer.py`'s row, and every other fact the test asks for
-- `Capability.MINE`, `Capability.CONNECT`, `Capability.DISCONNECT`, a
`Peer` (`peer.py`), and `setnetworkactive`, which is
`Capability.SUSPEND_NETWORK` -- is the adapters' own rather than another
step 5 mechanism. Core expects `NODE_P2P_V2` besides under its own
`--v2transport`, and the test expects it where the node declares
`Capability.V2TRANSPORT` (`tests/integration/p2p_node_network_limited_test.py`'s
own docstring). `btclib-node`'s cell is a counted skip, on
`Capability.MINE` on the released build and on `Capability.DISCONNECT`
on `main`. Measured apart from the test, on both builds: a `getdata` for
the oldest block the window holds is served and one for the block before
it disconnects, as on bitcoind; `setnetworkactive` and `getchaintips`
name no callback
([ISS btclib-node#1392](https://github.com/btclib-org/btclib-node/issues/1392),
[ISS btclib-node#1393](https://github.com/btclib-org/btclib-node/issues/1393));
`getnetworkinfo` answers no `localservices`
([ISS btclib-node#1394](https://github.com/btclib-org/btclib-node/issues/1394));
and the node's `version` signals `NODE_COMPACT_FILTERS` besides, which
bitcoind signals only under `-peerblockfilters`
([ISS btclib-node#1395](https://github.com/btclib-org/btclib-node/issues/1395)).

The option family's census is Core's `test/functional/` at `master`
`ed7dd7cf4e15`, run from this repository's root beside a Core checkout
at `../bitcoin`:

```shell
core=ed7dd7cf4e15
other='MiniWallet|assert_debug_log|mocktime|datadir_path|blocks_path'
other+='|chain_path|createwallet|getnewaddress|skip_if_no_wallet'
git -C ../bitcoin ls-tree --name-only "${core}" test/functional/ |
    sed -n 's|^test/functional/\([a-z][a-z0-9_]*\.py\)$|\1|p' |
    grep -v '^wallet_' |
    while read -r name; do
        grep -qwF "${name}" TF2.md && continue
        text=$(git -C ../bitcoin show "${core}:test/functional/${name}")
        grep -qE "[\"']-[a-z]" <<<"${text}" || continue
        grep -qE "${other}" <<<"${text}" && continue
        echo "${name}"
    done
```

A file is the option family's
([ISS 3](https://github.com/btclib-org/bitcoin-node-tests/issues/3))
where the option is all it asks for beyond what the adapters and `Peer`
already provide: an option `btclib-node` lacks, or one asking for no
capability, and no other step 5 mechanism. The command lists every Core
test file this ledger names nowhere, `wallet_*.py` aside
([ISS 45](https://github.com/btclib-org/bitcoin-node-tests/issues/45)),
that passes a string literal opening with `-` and a letter, and that
reaches neither MiniWallet, `assert_debug_log`, `setmocktime`, the
node's own files through `datadir_path`, `blocks_path` or `chain_path`,
nor a wallet. It skips a file this ledger names anywhere, whether or not
the ledger says where that file goes. Measured of this ledger rather than
following from the filter: every file the command lists against an empty
ledger and the table above gives no row has a sentence here saying where
it goes, which a later mention naming no home would break. Against this
ledger it lists nothing; against one naming none of the files below, it
lists those files, each going where its line says:

- `p2p_node_network_limited.py`, the row above, the option family's;
- `feature_proxy.py`, the rows above, ported on the proxy
  [ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47)
  builds;
- `interface_usdt_net.py`, a USDT tracepoint test
  ([ISS 48](https://github.com/btclib-org/bitcoin-node-tests/issues/48));
- `p2p_v2_encrypted.py`, whose `-v2transport` is `Capability.V2TRANSPORT`
  but whose peers speak BIP324 themselves, a transport `Peer` does not
  ([ISS 175](https://github.com/btclib-org/bitcoin-node-tests/issues/175));
- `rpc_getdescriptorinfo.py`, the row above, whose subject is the RPC
  rather than `-disablewallet`
  ([ISS 174](https://github.com/btclib-org/bitcoin-node-tests/issues/174)).

`feature_presegwit_node_upgrade.py`'s row keeps every assertion Core's
own file makes: a fresh chain with segwit inactive under
`-testactivationheight=segwit@N`; the height mined below it; a restart
naming a lower height the chain already runs past refused, with a
non-zero exit and a stderr equal to Core's own `expected_msg` whole, the
`ErrorMatch.FULL_TEXT` comparison `assert_start_raises_init_error` makes
by default; and, restarted with `-reindex` added, a chain one block short
of the lower height with segwit active. Each restart names `extra_args`
other than the ones the node last held, which `NodeAdapter.restart`
(`node.py`) takes for one start
([ISS 51](https://github.com/btclib-org/bitcoin-node-tests/issues/51)),
and the refused one is read the way `rpc_users_bitcoind_test.py` and
`feature_blocksdir_test.py` read theirs, a `RuntimeError`
carrying the node's stderr. Dropped is the empty stderr Core's own
`TestNode.stop_node` expects of every stop: a check its harness makes
around each stop rather than one this file makes, and `NodeAdapter.stop`
makes it for no test.

The blocks are Core's own shape rather than `MiniWallet.generate`'s: a
coinbase carrying the witness commitment and, segwit not yet active, no
witness nonce, which is what Core's own `generate` mines here
(`GenerateCoinbaseCommitment` and `UpdateUncommittedBlockStructures`,
`src/validation.cpp`). `CheckWitnessMalleation` refuses that pair once
segwit's rules apply, and that refusal is what stops the reindexed chain
short. A `MiniWallet` block carries neither, and a chain of them
reindexes to its full height instead, measured against the pinned
bitcoind; so this port builds Core's coinbase itself and submits it over
`submitblock`. `tests/integration/feature_presegwit_node_upgrade_test.py`'s
own docstring has the argument, and the wait for `getmempoolinfo`'s
`loaded` that Core's own start makes and `NodeAdapter.start` does not.
`btclib-node`'s cell is a counted skip on
`Capability.TEST_ACTIVATION_HEIGHT`, as the activation-height trio's
are.

`rpc_validateaddress.py`'s row is Core's own claim in full
([ISS 153](https://github.com/btclib-org/bitcoin-node-tests/issues/153)):
on a node started on the main chain, Core's own `self.chain = ""`, with
Core's own `-prune` value, every address of the file's own `INVALID_DATA`
answers `isvalid` false with the error and the `error_locations` its row
names, and every address of its `VALID_DATA` answers the `scriptPubKey`
its row names and neither the error nor its locations. `NodeAdapter`'s
own `chain="main"` (`node.py`) is what starts the node there
([ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63)).
Both tables are Core's own, copied into
`rpc_validateaddress_test.py` from the file at this row's pin,
so re-checking the pin is also what says whether the copy has gone
stale. `btclib-node`'s cell is a counted skip on
`Capability.VALIDATE_ADDRESS` (`capability.py`): `validateaddress` names
no callback in `btclib_node.rpc.callbacks`'s own dispatch table, on the
released build or on `main` (`btclib_node.py`'s own docstring has the
measurement).

`rpc_getdescriptorinfo.py`'s row is Core's own claim with its one option
left out ([ISS 174](https://github.com/btclib-org/bitcoin-node-tests/issues/174)):
every descriptor of the file's own table answers the same asked with its
checksum as without, answers its own checksummed form -- for a multipath
one, the first of the expansions its row names, with all of them as
`multipath_expansion` -- and the `isrange`, `issolvable` and
`hasprivatekeys` its row names; a missing argument, a wrong type, an
empty descriptor and a key padded with whitespace are each refused with
Core's own code and message. The option is `-disablewallet`, one
`capability.py`'s module docstring names as only bitcoind's to carry;
it is not this file's subject, so the port leaves it out rather than
making the row bitcoind only, and asks the session's shared
`bitcoind_adapter`, `getdescriptorinfo` being registered in
`src/rpc/output_script.cpp` rather than among the wallet's RPCs. Each
expected checksum is btclib's `descriptors.add_checksum`, which this
ledger's `descriptors.py` entry pairs with Core's `descsum_create`. The
descriptors and messages are Core's own, copied into
`rpc_getdescriptorinfo_test.py` from the file at this row's
pin, so re-checking the pin is also what says whether the copy has gone
stale. `btclib-node`'s cell is a counted skip on
`Capability.DESCRIPTOR_INFO` (`capability.py`): `getdescriptorinfo`
names no callback in `btclib_node.rpc.callbacks`'s own dispatch table,
on the released build or on `main` (`btclib_node.py`'s own docstring has
the measurement).

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

`feature_versionbits_warning.py` (`-alertnotify=<cmd>`) and
`rpc_signer.py` (`-signer=<cmd>`) each start a node that execs an
external command -- a shell one-liner writing to a file, a bundled mock
signer script -- and assert on what that process did. No adapter here
runs, tracks or verifies an external process a node itself spawns; both
are
[ISS 49](https://github.com/btclib-org/bitcoin-node-tests/issues/49)'s
own subject, "drives another binary", rather than this issue's.

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

The qualified rows ask what Core's own file does not and other Core
files rest on: `confirmed_only` for
[ISS 69](https://github.com/btclib-org/bitcoin-node-tests/issues/69),
`fee_rate` and TRUC for
[ISS 103](https://github.com/btclib-org/bitcoin-node-tests/issues/103).

`Capability.MINE` is what these rows' `btclib-node` cells skip on,
`confirmed_only` aside, the same shape the first family already takes
rather than a new question:
`mini_wallet.py`'s own mechanism produces exactly the fact `MINE` already
names -- "a block the node accepts as its own new tip, however it gets
there" -- by client-side construction over `submitblock` rather than a
node's own wallet. `BtclibNodeAdapter` declares it only on a build
that connects a submitted block with no peer -- `main` from the commit
closing
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
on -- and its own `mine` is `MiniWallet.generate`. The released build
does not, so each cell is the skip. On a `main` declaring it, each row
is a body run against both nodes (`tests/integration/conftest.py`'s own
module docstring): the unqualified row passes, and `fee_rate` and TRUC
fail on an RPC that `main` does not serve -- `getmempoolentry`
([ISS btclib-node#1397](https://github.com/btclib-org/btclib-node/issues/1397))
and `decoderawtransaction`
([ISS btclib-node#1398](https://github.com/btclib-org/btclib-node/issues/1398)).
With that call removed, TRUC fails next on a TRUC transaction over
`TRUC_MAX_VSIZE` that `main` accepts
([ISS btclib-node#1399](https://github.com/btclib-org/btclib-node/issues/1399)).

`confirmed_only` has the node itself confirm one of its coins, over
`generateblock`, so it asks for `Capability.GENERATE` ahead of
`Capability.MINE` -- a node taking a client's block over `submitblock`
builds none itself, `capability.py` having the distinction -- and its
`btclib-node` cell is that skip on both builds: `btclib_node`'s own
dispatch table (`src/btclib_node/rpc/callbacks.py`) names no
`generateblock`, at the released build or at `main`
([ISS btclib-node#1396](https://github.com/btclib-org/btclib-node/issues/1396)).
With that call removed, `main` fails the body next on
`MiniWallet.resync`'s `gettxout`
([ISS btclib-node#1388](https://github.com/btclib-org/btclib-node/issues/1388)).

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
(`utxo_to_spend`, spending a caller-named coin in place of the one
`get_utxo` would pick) and `resync` (re-reading the tip after a chain
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

Both rows are one body run against both nodes
(`tests/integration/conftest.py`'s own module docstring), each reading a
block's own transactions off `getblock`'s raw form, the only one
btclib-node serves. A `main` declaring `Capability.MINE` runs each and
fails it. In `mempool_spend_coinbase.py` the immature spend is refused,
but as "Invalid signatures or script" rather than Core's own
`bad-txns-premature-spend-of-coinbase`
([ISS btclib-node#1328](https://github.com/btclib-org/btclib-node/issues/1328)).
In `mempool_resurrect.py` the orphaned spends do return to the mempool,
and the body then stops at `MiniWallet.resync`, which asks `gettxout`,
an RPC that build does not serve
([ISS btclib-node#1388](https://github.com/btclib-org/btclib-node/issues/1388)).

`rpc_generate.py`, `rpc_signrawtransactionwithkey.py` and
`rpc_scantxoutset.py` are ported, their own rows above, each one body run
against both nodes (`tests/integration/conftest.py`'s own module
docstring). Each drives the RPC it is named for as its own subject --
`generatetoaddress` and `generateblock`, `signrawtransactionwithkey`,
`scantxoutset` -- with `MiniWallet` mining the coins and funding the
outputs that RPC then answers for, and each asks for that RPC's own
capability first, ahead of `Capability.MINE` wherever it needs a coin:
`Capability.GENERATE`, `Capability.SIGN_RAW_TRANSACTION` and
`Capability.SCAN_UTXO_SET` (`capability.py`). `btclib_node`'s own dispatch table
(`src/btclib_node/rpc/callbacks.py`) names none of those RPCs, at the
released build or at `main`, so each `btclib-node` cell is that skip on
both, `main`'s own `MINE` never reached
([ISS btclib-node#1404](https://github.com/btclib-org/btclib-node/issues/1404),
[ISS btclib-node#1396](https://github.com/btclib-org/btclib-node/issues/1396),
[ISS btclib-node#1400](https://github.com/btclib-org/btclib-node/issues/1400),
[ISS btclib-node#1406](https://github.com/btclib-org/btclib-node/issues/1406)).
What each port builds with btclib where Core asks the node, and what it
drops, is in its own `tests/integration/<file>_test.py` docstring.
`rpc_scantxoutset.py`'s `bitcoind` cell is build-dependent: the pinned
file expects `start` with a null scan-object list refused as a missing
argument, which bitcoind does from `v32.0rc1` on, the first tag carrying
bitcoin/bitcoin@aeca0610865ede44004b42a16ef6318245fe0644, while the
pinned release refuses the null as a value of the wrong type; the
bitcoind module reads `getnetworkinfo`'s own `version` and expects
whichever the running build answers.

`mining_template_verification.py` is ported, its own row above, one body
run against both nodes (`tests/integration/conftest.py`'s own module
docstring). Its subject is `getblocktemplate` in BIP23's `proposal`
mode, checking a block without storing it, so it asks for
`Capability.BLOCK_PROPOSAL` (`capability.py`) ahead of
`Capability.MINE`, `MiniWallet` mining the chain the proposals build on
and the transaction they carry. `getblocktemplate` is not in
`btclib_node`'s own dispatch table, at the released build or at `main`,
so the `btclib-node` cell is that skip on both, `main`'s own `MINE`
never reached
([ISS btclib-node#1427](https://github.com/btclib-org/btclib-node/issues/1427)).
With that ask removed, `main` fails the body next on `getblock` at its
default verbosity, which it refuses
([ISS btclib-node#1428](https://github.com/btclib-org/btclib-node/issues/1428)).
The blocks it proposes are built with btclib in the shape of Core's own
`create_block` and `create_coinbase` (`blocktools.py`), and what the
port changes from Core's file is in its own
`tests/integration/mining_template_verification_test.py` docstring.

`mempool_accept_wtxid.py` and `rpc_orphans.py` are ported, their own
rows above, each one body run against both nodes, `MiniWallet` building
the transactions and a `Peer` (`peer.py`) standing in for Core's own
`P2PInterface`: in `mempool_accept_wtxid.py` it records which wtxid the
node announces and requests each, in `rpc_orphans.py` it sends a child
ahead of its own parent. What each port builds with btclib where Core's
framework builds it -- `build_malleated_tx_package`, `tx_in_orphanage`,
`P2PTxInvStore` -- is in its own `tests/integration/<file>_test.py`
docstring.

`rpc_orphans.py` asks for `Capability.ORPHANAGE` (`capability.py`) ahead
of `Capability.MINE` wherever it builds a transaction, and its
`btclib-node` cell is that skip on both builds: `getorphantxs` is not
in `btclib_node`'s own dispatch table, and no source file there names an
orphan
([ISS btclib-node#1420](https://github.com/btclib-org/btclib-node/issues/1420)).
`mempool_accept_wtxid.py` asks for `Capability.MINE` alone, its subject
being `sendrawtransaction`, `testmempoolaccept` and the announcement
that follows, and btclib-node serves both RPCs on either build. A
`main` declaring `MINE` runs it and fails on `getmempoolentry`, which it
does not serve
([ISS btclib-node#1397](https://github.com/btclib-org/btclib-node/issues/1397)).
With that call removed, it fails next on `getmempoolinfo`'s missing
`unbroadcastcount`
([ISS btclib-node#1421](https://github.com/btclib-org/btclib-node/issues/1421)),
and with those reads removed too, `testmempoolaccept` allows both the
child the mempool holds and the one sharing its txid, where bitcoind
refuses each
([ISS btclib-node#1422](https://github.com/btclib-org/btclib-node/issues/1422)).

`mempool_cluster.py` and `rpc_packages.py` also drive MiniWallet alone at
first read, but each also restarts its node with an option --
`-limitclustersize`/`-limitclustercount` and
`-maxmempool`/`-persistmempool` in turn -- that `btclib-node`'s own
`cli.py` does not register, so the option family's own exclusion reaches
them too: ISS 14's, same as the wallet, log, disk and clock files below.
`rpc_packages.py` alone also calls `test_framework.mempool_util.fill_mempool`,
now built as `mempool_util.fill_mempool`
([ISS bitcoin-node-tests#70](https://github.com/btclib-org/bitcoin-node-tests/issues/70)).
`mempool_sigoplimit.py`, named alongside them for the same reason, is
ported below, its own paragraph naming what of it is kept.

`p2p_tx_privacy.py` asks for MiniWallet alone too, and is ported, its
own row above: a second p2p connection holds its handshake open while
the first sends a transaction, and a `wtxid` announcement is withheld
from the second until its own handshake completes. Its spy is a `Peer`
(`peer.py`) sending `version` and `wtxidrelay` by hand and holding back
its `verack`, the way `tests/integration/p2p_timeouts_test.py` holds a
handshake open rather than calling `Peer.handshake`; what the port adds
to Core's own file is in `tests/integration/p2p_tx_privacy_test.py`'s
docstring. Its `btclib-node` cell is `Capability.MINE`'s skip on the
released build. The `main` half is read from btclib-node's own source
at `9ae620c2` rather than run: `P2pManager.promote_connection`, called
from `callbacks.verack` alone, is what moves a connection into the
`connections` table `DownloadManager` queues each announcement against,
so a connection still in its handshake is queued none. Every other
MiniWallet-touching file asks for a wallet (`createwallet`, out for good,
rule 3's own exclusion), the log, the disk or the clock alongside
MiniWallet, or an option -- ISS 14's once every step-5 mechanism lands,
the wallet files excepted.

`mempool_package_rbf.py` and `mempool_truc.py`, the family's other own
mempool-policy files, are read this round too and stay open, as
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s:
each also sets an option, `-maxmempool` at every start of Core's own
`mempool_package_rbf.py`, which its `fill_mempool` needs, and a restart's
own in `mempool_truc.py`. `mempool_package_rbf.py` drives a second node
in Core's own file, never read from -- its own `sync_all` calls confirm
nothing either test asserts on -- dropped as a smaller claim, so what
actually blocked it was the same `fill_mempool` `rpc_packages.py` needed
above, now built
([ISS bitcoin-node-tests#70](https://github.com/btclib-org/bitcoin-node-tests/issues/70)),
and the caller-chosen fee, sequence and TRUC's own non-default
transaction version its own self-transfers pass, which
`create_self_transfer` takes
([ISS 103](https://github.com/btclib-org/bitcoin-node-tests/issues/103)).
`mempool_truc.py` needs no second node and no option at its own base
`set_test_params` (`self.extra_args = [[]]`), but several of its own
subtests restart with one in turn
(`-limitclustercount`/`-limitclustersize`/`-acceptnonstdtxn`/`-minrelaytxfee`/`-persistmempool`),
which `NodeAdapter.restart` (`node.py`) takes for one start; the
caller-chosen fee rate and TRUC's own transaction version its own
self-transfers pass are what `create_self_transfer` and
`create_self_transfer_multi` take
([ISS 103](https://github.com/btclib-org/bitcoin-node-tests/issues/103)),
so it is an open candidate for a port of its own.

`feature_dersig.py`, `feature_cltv.py` and `feature_csv_activation.py`
are ISS 14's own softfork-activation-height trio, the option and
MiniWallet families' first tests to need both mechanisms together:
`-testactivationheight=<deployment>@<height>` (`Capability.TEST_ACTIVATION_HEIGHT`,
`capability.py`) holds one buried deployment inactive until a chosen
height, and `MiniWallet.generate` (`Capability.MINE`) mines to it with
no node wallet. Each is a smaller claim than Core's own file, declared
rather than silent, the module docstrings of `feature_cltv_test.py`,
`feature_csv_activation_test.py` and `feature_dersig_test.py`
carrying the full argument: kept is `getdeploymentinfo`'s own transition
one block before the configured height, and, for `feature_dersig.py` and
`feature_cltv.py`, the buried-deployment version floor a too-low
block version trips once the deployment is active -- `bad-version(0x...)`,
`submitblock`'s own answer and, on a row of its own, the same wording in
bitcoind's own debug log. `feature_dersig.py`'s own non-DER signature is
kept too, on a row of its own
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)):
coinbases pay `mini_wallet.py`'s `RAW_P2PK_SCRIPT_PUB_KEY`, Core's own
`RAW_P2PK` output, `raw_p2pk_script_sig` signs their spends, and the
non-DER one is mined before activation and refused after it by
`testmempoolaccept` and `submitblock` alike. `feature_cltv.py`'s own
`OP_CHECKLOCKTIMEVERIFY` failure reasons are kept too, under the same
issue, on rows of their own. They need no signature: coinbases pay
Core's own `RAW_OP_TRUE` output, a bare `OP_TRUE`, and each spend's
scriptSig starts with what fails the opcode for one reason. The spends
are mined in the block before the configured height and refused in a
block at it, which pins where the script rule starts. The mempool and
block rows run on regtest's own default activation, BIP65 active from
the first block after genesis: `testmempoolaccept` refuses each, the
node running with Core's own `-acceptnonstdtxn`
(`Capability.ACCEPT_NON_STANDARD`) since the spends are non-standard;
and `submitblock` refuses a block carrying each and accepts the spend
CLTV admits. Needing no `-testactivationheight`,
`feature_cltv.py`'s block row asks `btclib-node` for `Capability.MINE`
alone. `feature_csv_activation.py`'s own body is kept too, under the
same issue, on a row of its own: BIP68's relative lock times, BIP112's
`OP_CHECKSEQUENCEVERIFY` and BIP113's median-time-past cutover, at
Core's own configured height. Its coins are `RAW_P2PK` ones, signed as
`feature_dersig.py`'s are, and each BIP112 spend has the opcode, and
the argument it checks where there is one, prepended to that signature.
Every spend is accepted in the block before the configured height, and
BIP113's is refused at it, which pins where BIP113 starts; BIP68's and
BIP112's refusals follow a few blocks on, as in Core's own file. Core's
`invalidateblock` (`Capability.INVALIDATE_BLOCK`) takes each accepted
block back off, so that the next check builds on the same tip.
`feature_csv_activation.py` gains no version-floor row the way its
siblings do: `src/validation.cpp`'s own `ContextualCheckBlockHeader`
reads only `DEPLOYMENT_HEIGHTINCB`, `DEPLOYMENT_DERSIG` and
`DEPLOYMENT_CLTV` for its version check, `DEPLOYMENT_CSV` never joining
it, so there is no such refusal for CSV's own activation to produce.
Every other `btclib-node` cell across the trio is a counted skip before
`require` reaches `Capability.MINE`, which every row also needs:
`feature_cltv.py`'s mempool row on `Capability.ACCEPT_NON_STANDARD`
(`btclib_node.py`'s own docstring has the measurement), and the rest on
`Capability.TEST_ACTIVATION_HEIGHT` -- measured against `cli.py`'s
registered options, `_build_parser` on the released build and `_OPTIONS`
on `main`, `-testactivationheight` is not one of its registered flags.

`feature_nulldummy.py`'s row is every step of Core's own file, in its
own order ([ISS 64](https://github.com/btclib-org/bitcoin-node-tests/issues/64)):
`-testactivationheight=segwit@N` holds NULLDUMMY inactive with segwit
until the configured height, and each step puts a multisig spend whose
dummy element is empty or `OP_TRUE`, in a P2SH scriptSig or a
P2SH-P2WSH witness, to `sendrawtransaction`, to `submitblock` or to
both. The multisig requires one signature, as Core's own does, and the
test signs each spend with btclib -- `btclib.script.sig_hash` and
`btclib.ecc.dsa.sign_` -- so that a node reads the dummy beneath a
signature ([ISS 165](https://github.com/btclib-org/bitcoin-node-tests/issues/165)).
Neither sighash commits to the dummy, so tampering it leaves the
signature valid; a signature bitcoind refuses fails the row on
`SCRIPT_ERR_SIG_NULLFAIL` instead, a finding for btclib's own tracker.
The test builds each spend directly as a `btclib.tx.Tx`, the
way `mempool_sigoplimit.py`'s own port spends its witness script, and
the coins spent first are coinbases paying the multisig: every
`MiniWallet` coin is spent through a witness, and bitcoind refuses a
block carrying one before segwit activates.
`tests/integration/feature_nulldummy_test.py`'s own docstring
has what else differs from Core's own file.
The `btclib-node` cell is a counted skip on
`Capability.TEST_ACTIVATION_HEIGHT`, as the trio's are.

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
own mode) differently from bitcoind on the released build, which is a
disagreement rather than a missing capability. Measured live against
`btclib-node` `main` `b853eb46`, before the fix: the chain directory and
every store directory under it, and
`history.log` (`btclib_node.py`'s own `log_path`, the fact
`debug_log_path` names for bitcoind), all come up at the operating
system's own umask default -- group and other readable, the directories
executable too -- rather than an owner-only mode either the directory
creation or the store construction sets. Filed as
[ISS btclib-node#1198](https://github.com/btclib-org/btclib-node/issues/1198).

`rpc_createmultisig.py`'s rows are a smaller claim than Core's own file
([ISS 4](https://github.com/btclib-org/bitcoin-node-tests/issues/4),
found by [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
census) only by `test_sortedmulti_descriptors_bip67`, which reads its
vectors from Core's own `data/rpc_bip67.json`, a vendored fixture this
repository does not carry.

The first row is construction: `createmultisig` answering the address,
redeemScript and descriptor btclib builds, across every
`(nsigs, nkeys, output_type)` Core's own `m_of_n` list names; falling
back to a legacy address with a warning where a key is uncompressed; and
`test_multisig_script_limit`'s own checks -- the "correct encoding" of
every key count up to `MAX_PUBKEYS_PER_MULTISIG`, the address of a
multisig past `OP_16`'s own count, and the refusals of too large a
legacy redeemScript and of too many keys. Past `OP_16`'s count
`ScriptPubKey.p2ms` and btclib's descriptor parser both refuse the
script
([ISS btclib-org/btclib#2348](https://github.com/btclib-org/btclib/issues/2348)),
so the port builds it from its own items instead, with
`btclib.script.script.serialize`. It needs no coin, no mining and no node
wallet, so it carries no `Capability`. Its `btclib-node` cell is
**bitcoind only** for a reason other than an option's: `createmultisig`
is not in `btclib_node`'s own dispatch table
(`src/btclib_node/rpc/callbacks.py`, measured on the released build,
`422d2640`, and at `main` `4e155386` alike), so the RPC is absent there.

The (spend) row is `do_multisig`'s spend half, every call Core's own
file makes of it, with `test_combinerawtransaction_preconditions`
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)):
`MiniWallet` funds each multisig output, and the node signs a spend of it
with disjoint sets of its keys and merges the partial signatures, over
`signrawtransactionwithkey` and `combinerawtransaction`
(`Capability.SIGN_RAW_TRANSACTION`). What Core asks the node to build
without signing -- the output, the unsigned spend -- btclib builds.
`combinerawtransaction` refuses a single transaction, or one differing
from the first, only from `6d86184a8bcc` on, a commit the pinned release
does not carry: it accepts both. So the row reads `getnetworkinfo`'s
`version` against the first release tagged with that commit, and on an
earlier build asserts what the pinned release answers instead: an
undecodable transaction and an empty list refused, the latter in its own
shorter wording, and a single transaction returned as it came. A `master`
build from that commit's merge until its version reached that release's
own reports an earlier version and refuses all the same, so the row fails
against such a build. btclib-node serves neither RPC on either
build
([ISS btclib-node#1400](https://github.com/btclib-org/btclib-node/issues/1400)),
so it skips on the capability.

[ISS 6](https://github.com/btclib-org/bitcoin-node-tests/issues/6)'s own
remaining files, `p2p_fingerprint.py` and `p2p_invalid_block.py`, are
not in this batch: each needs `Capability.MINE` and a raw peer
conversation well beyond a handshake -- `p2p_fingerprint.py` a
headers-first reorg onto a fork built and held back rather than
submitted, `p2p_invalid_block.py` a legacy `OP_TRUE` bare coinbase and
scriptSig distinct from `MiniWallet`'s own P2TR shape, plus merkle-root
malleability and a `getdata`-driven send/reject cycle matched against
`Capability.DEBUG_LOG`'s own wording. Neither mechanism is this batch's
to build. `p2p_fingerprint.py` asks step 5 for the clock alone, and ISS 6's
own comment has it ported citing that issue, which stays closed on its
mechanism. `p2p_invalid_block.py` asks for more: the log for every refusal
it checks, through `send_blocks_and_test`'s own `reject_reason`, and the
`noban` permission Core's own `noban_tx_relay` grants, which keeps its
peer connected through the refusals -- so it is
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s,
the log family's census above.

`p2p_invalid_block.py` is ported, its rows above each Core's whole run
as a body over a fresh node in
`tests/integration/p2p_invalid_block_test.py`, whose module docstring has
what differs from Core's file. The (wire) row reads each block's
acceptance or refusal off `getbestblockhash`, and the (log) row asserts
besides each refusal's own reject reason in the node's log, over
`DEBUG_LOG`. Both ask for `MINE`, the node mining the blocks that mature
the coinbase the run spends, and `CLOCK`, for the block ahead of the
node's clock; the node restarts with the `noban` permission, which asks
for no capability. Each `bitcoind` cell is one verdict for the pinned
release and for Core's `master`. `btclib-node`'s cell on each row is a
counted skip on `MINE` on the released build, and on `CLOCK`, which no
build declares, on a build past
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071).

`p2p_timeouts.py`, `p2p_ping.py` and `mempool_expiry.py` are
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s,
each run on a single node that no step has dial out, and each combining
an option with the clock and either the log or `MiniWallet`: `-peertimeout` is
`Capability.PEER_TIMEOUT` and `-mempoolexpiry` `Capability.MEMPOOL_EXPIRY`
(`capability.py`). Each is Core's own claim in full, as Core's default
run makes it, and each body module's own docstring
(`tests/integration/<file>_test.py`) has how every fact is reached.
`p2p_timeouts.py` and `p2p_ping.py` give the wire and the log a row
each, the log family's rule, and `p2p_timeouts.py`'s refused start under
a non-positive `-peertimeout` has a row of its own. Both start their
node with BIP324 and automatic connections turned off, as Core's harness
starts every node and `BitcoindAdapter` does not;
`tests/integration/p2p_timeouts_test.py`'s own docstring has the options
and why each is there. `mempool_expiry.py` checks Core's
default expiry and then, over the same node restarted, its custom one.
Every `btclib-node` cell is a counted skip on the option's capability,
asked for first: `cli.py` registers neither option, on the released
build or on `main` (`btclib_node.py`'s own docstring), and neither build
names `setmocktime` in its RPC dispatch table.

`feature_includeconf.py` and `feature_reindex_init.py` are
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s,
each an option and the disk together, each test building its node over a
data directory of its own through `make_adapter`
(`tests/integration/conftest.py`). `feature_includeconf.py` gives each of
Core's refusals, and the warning an `includeconf` inside an included file
draws, a row of its own, and the order the files are read in another.
That row observes the order through `-uacomment`, as Core does; the
others write no `uacomment` line, matching the whole of the node's stderr
against Core's own words. `tests/integration/feature_includeconf_test.py`'s
own docstring has what else differs from Core's file. Only the order row
asks for a capability, so `btclib-node` runs the rest on both builds. The
released build refuses `-includeconf` on the command line in argparse's
own words
([ISS btclib-node#1116](https://github.com/btclib-org/btclib-node/issues/1116)),
and a build past that fix still refuses it as an unknown option, Core's
wording arriving later
([ISS btclib-node#1409](https://github.com/btclib-org/btclib-node/issues/1409)).
The released build drops a nested `includeconf` in silence
([ISS btclib-node#1403](https://github.com/btclib-org/btclib-node/issues/1403)),
and refuses a missing included file in words of its own. The missing-file
row is bounded at
[ISS btclib-node#1187](https://github.com/btclib-org/btclib-node/issues/1187),
which is about reading `-datadir` and `-conf` lexically normal, because
the pull request fixing it, btclib-org/btclib-node#1300, also brought
Core's "Failed to include configuration file" wording. A build past
[ISS btclib-node#1409](https://github.com/btclib-org/btclib-node/issues/1409)
and before
[ISS btclib-node#1402](https://github.com/btclib-org/btclib-node/issues/1402)
refuses the double negative `-noincludeconf` given a false value after
writing a warning about it to stderr, where bitcoind writes the refusal
alone. `main` agrees with bitcoind on each of them.
The order row is a counted skip on `Capability.UA_COMMENT`, which neither
build declares. `feature_reindex_init.py` is Core's own claim in full, its
`btclib-node` cell a counted skip on `Capability.REINDEX_AFTER_FAILURE`,
asked for first: `cli.py` registers no `-test` on either build
(`btclib_node.py`'s own docstring).

`feature_reindex.py` and `feature_reindex_readonly.py` are ISS 14's too,
the option, the disk and the log together, each test building its node
over a data directory of its own through `make_adapter` as those above
do. `feature_reindex.py` gives each step of Core's `run_test` a row: the
restarts alternating `-reindex` and `-reindex-chainstate`, each back at
the height mined; a block file holding a block ahead of its parent,
reindexed with the out-of-order block and its child logged; and a
reindex stopped once it has started, whose next start without
`-reindex` opens its block filter index rather than wiping it. Each
asserts more than Core's file, so that a node ignoring the option or the
interruption cannot pass: a log line each restart writes only when the
option took effect, the interruption's own line, and the resumed
reindex finishing.
`feature_reindex_readonly.py` is Core's own claim, a reindex of a block
file the node cannot write to, taken with the file's mode alone: Core
also tries the immutable flag, which only a run as root needs, and this
asserts instead that the file is unwritable before the restart.
Each module docstring has what else differs from Core's file. The
out-of-order step's log lines are in Core's `reindex` category, which
`BitcoindAdapter` enables (`bitcoind.py`'s own `_command`). Every
`btclib-node` cell is a counted skip on the new `Capability.REINDEX`,
asked for first: neither build takes `-reindex` or `-reindex-chainstate`
([ISS btclib-node#1415](https://github.com/btclib-org/btclib-node/issues/1415)).

`p2p_message_capture.py` and `feature_blocksxor.py` are ISS 14's too,
the option and the disk together, `feature_blocksxor.py` with MiniWallet
besides, as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags them; each test builds its nodes through `make_adapter`, each
node's option given from its first start. `p2p_message_capture.py` is
Core's own claim, a peer's messages written to disk under
`-capturemessages` in the record format Core's `mini_parser` reads,
each record's type checked against the ones a `btclib.p2p` payload
class names rather than against Core's `MESSAGEMAP`. It also asserts
the capture directory is named for the peer's own address and holds the
types the peer sent and the node answered with, so that a node writing
some other file there cannot pass.
`feature_blocksxor.py` is Core's own claim, the block and undo files a
node wrote under `-blocksxor` XORed back to plain, a restart turning the
option off refused while the key is stored, and one allowed once the key
file is gone verifying the chain and writing an all-zero key. That last
step, and the option turned on, pass on a node ignoring it: the first is
what Core's `InitBlocksdirXorKey` does anyway for a block directory
holding files and no key file, and the second is Core's default. So the
test also asserts the first block file obfuscated under the key, and an
all-zero key written by a fresh node started with the option off.
Each module docstring has what else differs from Core's file. Every
`btclib-node` cell is a counted skip on the option's new capability,
`Capability.CAPTURE_MESSAGES` or `Capability.BLOCKS_XOR`, asked for
first: `cli.py` registers neither option on either build
(`btclib_node.py`'s own docstring).

`feature_remove_pruned_files_on_startup.py` is ISS 14's too, the option
and the disk together, as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags it; its test builds its node through `make_adapter`, under Core's
`-fastprune` and `-prune` from the first start. It is Core's own claim
on a platform that deletes an open file: `pruneblockchain` deletes the
oldest block and undo files, among them the ones the test holds open,
they stay gone across a restart, and a restart with `-reindex` leaves
only the files a reindex from genesis writes.
`tests/integration/feature_remove_pruned_files_on_startup_test.py`'s own
docstring has what differs from Core's file. The `btclib-node`
cell is a counted skip on `Capability.FASTPRUNE`, asked for first:
`cli.py` registers no `-fastprune` on either build.

`feature_startupnotify.py` is ISS 14's too, the option and the disk
together, as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags it; its test builds its node through `make_adapter`. It is Core's
own claim: a start without `-startupnotify` writes no file, and a
restart given it runs the command once, which appends to a file inside
the data directory, and answers RPC.
`tests/integration/feature_startupnotify_test.py`'s own docstring has
what differs from Core's file. The `btclib-node` cell is a counted skip
on `Capability.STARTUP_NOTIFY`: `cli.py` registers no
`-startupnotify` on either build
([ISS btclib-node#1449](https://github.com/btclib-org/btclib-node/issues/1449)).

`rpc_dumptxoutset.py` is ISS 14's too, the clock and the disk together,
as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags it; its test builds its node through `make_adapter`. It keeps
every check of Core's but the hashes Core asserts as constants: the
block hash, the file's SHA256 and `txoutset_hash` depend on the coinbase
the build writes, and the commit this row pins changed that coinbase and
every one of them. The test asserts each against the same node instead:
`getblockhash` at the tip's height, the file's metadata and a second
dump writing the same bytes, and `gettxoutsetinfo`'s own
`hash_serialized_3`. The pinned release refuses a dump at a height a
fork also reaches, so the bitcoind cell reads which the running build
does from its own version.
`tests/integration/rpc_dumptxoutset_test.py`'s own docstring has what
else differs from Core's file. The `btclib-node` cell is a counted skip
on `Capability.DUMP_UTXO_SET`: no source file names `dumptxoutset` on
either build
([ISS btclib-node#1471](https://github.com/btclib-org/btclib-node/issues/1471)).

`feature_loadblock.py` is ISS 14's too, the option and the disk
together, as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags it; its test takes its nodes from the cluster fixture. It is
Core's own claim: a node restarted with `-loadblock` naming a file of
the first node's chain reaches that node's height and best block.
Core writes the file with `contrib/linearize/`'s own scripts, which are
Core's source tree rather than the release, as `tool_utxo_to_sqlite.py`
below has it; so the test writes the file itself, in the format
`linearize-data.py` writes, from the blocks `getblock` serializes.
`tests/integration/feature_loadblock_test.py`'s own docstring has what
else differs from Core's file. The `btclib-node` cell is a counted skip
on `Capability.LOAD_BLOCK`: no source file names `loadblock` on either
build, reading Core's block files being left out by decision
([ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)).

`feature_port.py` is ISS 14's too, the option and the log together, as
[ISS 14's census](https://github.com/btclib-org/bitcoin-node-tests/issues/14#issuecomment-5839832569)
tags it; its test builds its node through `make_adapter`. It is Core's
own claim: a node restarted with `-port` listens on every address at the
last port given and on the loopback address at the port after it, a
`-bind` naming a port overrides `-port`, a `-bind` naming none takes
`-port`'s, an onion bind naming none takes the port after it, and a
`-port` out of range stops the start with Core's own error.
`BitcoindAdapter` passes a `-bind` of its own, so the bitcoind test
builds a subclass leaving it out, as Core's own test keeps its
framework's off.
`tests/integration/feature_port_test.py`'s own docstring has what else
differs from Core's file. The `btclib-node` cell is a counted skip on
`Capability.LISTEN_ADDRESS`: `cli.py` registers no `-bind` on either
build, and the node binds no onion listener
([ISS btclib-node#1257](https://github.com/btclib-org/btclib-node/issues/1257)).

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
`btclib-node` declares `DISCONNECT` on no build measured, filed as
[ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193),
and `BAN` only on a build past
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088),
the `rpc_setban.py` paragraph below.

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
`v2transport_option_test.py`, passes `True`. Measured against
the fix: the mixed-cluster test below, which timed out before it and
passes after, on every `btclib-node` build measured.

`rpc_setban.py` is ported, its own rows above. Core's own file restarts
a node repeatedly, some of those with different `extra_args` than it
started with and some with the same. The different-`extra_args`
restarts -- the `-whitelist` noban-permission section and the
`-bantime` section -- are `NodeAdapter.restart` (`node.py`) given its
own `extra_args`, which it uses for that start alone, the way Core's
own `restart_node(i, extra_args)` does
([ISS bitcoin-node-tests#51](https://github.com/btclib-org/bitcoin-node-tests/issues/51)):
a banned peer connecting once the node is restarted with its address
whitelisted, `getpeerinfo` naming `noban` among its permissions while
`listbanned` still lists the ban; and a ban added after a restart with
`-bantime` given that duration. The same-`extra_args` restarts are
`restart` given none: a ban surviving a plain restart, checked against
`listbanned` before the refused reconnection is attempted at all
([ISS 94](https://github.com/btclib-org/bitcoin-node-tests/issues/94)).
The reconnection is then Core's own, an `addnode ... "onetry"` inside
`assert_debug_log`: bitcoind's own `CreateNodeFromAcceptedSocket`
(`src/net.cpp`) logs `dropped (banned)` as it refuses the accepted
socket, and the dialling node's `getpeerinfo` stands in for Core's wait
on that node's own log for the disconnect. Reconnection succeeds again
once the ban is lifted. Kept alongside them: a live connection dropping the
moment `setban` matches its address, `node.wait_until_disconnected`
standing in for Core's own wait on `is_connected_to` going false; and
the non-IP address check, which needs no second node at all.
`Capability.BAN` is `btclib-node`'s counted skip on every row on the
build, and `btclib_node.py`'s own `_serves_ban_list` probe declares it on
a build past
[ISS btclib-node#1088](https://github.com/btclib-org/btclib-node/issues/1088)
([ISS 140](https://github.com/btclib-org/bitcoin-node-tests/issues/140)):
there each row is one body run against both nodes
(`tests/integration/conftest.py`'s own module docstring). The restart row
skips on `Capability.DEBUG_LOG`; the ban and `-bantime` rows pass; the
noban row's `-whitelist` is refused
([ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320));
and the non-IP row's onion address is refused by a build before
[ISS btclib-node#1218](https://github.com/btclib-org/btclib-node/issues/1218)
and banned and unbanned by a build past it.

`p2p_disconnect_ban.py`'s "Test disconnectnode RPCs" section is ported,
its own row above: a pair of nodes connected both ways, `disconnectnode`
refusing an address and a node id given together and an address no
peer has, then dropping a peer by address, the pair reconnecting, and
dropping a peer by node id. `Capability.DISCONNECT` is `btclib-node`'s
counted skip on every build,
[ISS btclib-node#1193](https://github.com/btclib-org/btclib-node/issues/1193)
being why. The file's `setban` half is not ported: it reads
`ban_duration` and `time_remaining` under `setmocktime`, waits for
"Recreating the banlist database" in `debug.log`, and deletes
`banlist.json` from the data directory -- the clock, log and disk
families beside node-linking, which makes it
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s.

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
which only some `btclib-node` builds declare (`btclib_node.py`'s own
docstring): nothing here asks the connecting side to mine anything of
its own.

Re-run against btclib-node's own `main` at `26bac0f5b78c`, a build past
every issue the table's fail cells name:
`p2p_invalid_messages_dropped_btclib_node_test.py`'s msgtype, checksum
and duplicate-version rows, `p2p_getdata_btclib_node_test.py`'s row,
`p2p_invalid_messages_misbehaving_btclib_node_test.py`'s oversized-`inv`
row, `p2p_invalid_messages_addrv2_btclib_node_test.py`'s addrv2-empty
and addrv2-long rows, and
`feature_posix_fs_permissions_btclib_node_test.py`'s row all pass. The
`main` job (`node-integration.yml`'s own `btclib-node-main`) is what
this run came from, and it gates nothing (`CONTRIBUTING.md`'s *What
gates a merge, and what only reports*).

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
  `mempool_reorg.py` (MiniWallet, `setmocktime`, `-whitelist`),
  `mining_basic.py` (MiniWallet, `setmocktime`, `-blockmaxweight`,
  `-prune`), `p2p_segwit.py` (MiniWallet, log, `-testactivationheight`),
  `feature_bip68_sequence.py` (MiniWallet, `setmocktime`,
  `-testactivationheight`) and `rpc_rawtransaction.py` (MiniWallet,
  `-txindex`, `-prune`): ISS 14's.
- `rpc_txoutproof.py` (MiniWallet, `-txindex`): ISS 14's, and it also
  needs `sync_txindex`, Core's own wait for a `-txindex` to catch up,
  which is a different primitive from
  `wait_until_tips_agree`/`wait_until_mempools_agree` and is not built
  by this issue.
- `p2p_v2_transport.py` (`-v2transport`, log, a raw socket): ISS 14's,
  on bitcoind alone, `Capability.V2TRANSPORT` being `BitcoindAdapter`'s
  and not `btclib-node`'s
  ([ISS btclib-node#1190](https://github.com/btclib-org/btclib-node/issues/1190)).
- `p2p_blockfilters.py` (`-blockfilterindex`, `-peerblockfilters`, log,
  and BIP157's own `getcfilters`/`getcfheaders`/`getcfcheckpt` from a
  raw peer): ISS 14's.
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

Both files' own `btclib-node` cells are a counted skip on their own
option capability alone, ahead of `Capability.MINE`: neither
`-limitclustercount` nor `-limitclustersize` is one of `cli.py`'s
registered flags, on the released build or on `main`.
`mempool_updatefromblock.py`'s chain-length case asks for
`Capability.GENERATE` after its option capability and ahead of
`Capability.MINE`, for its own `generateblock`.

`p2p_leak_tx.py`'s own rows are the clock and MiniWallet families
together, each subject its own pytest function over `Peer` and
`NodeAdapter` rather than Core's own
`P2PInterface`/`P2PDataStore`/`P2PTxInvStore`. "in block" is Core's own
`test_tx_in_block`: a `getdata` built from the `inv` the node announces,
sent only after the transaction has been mined into a block, is still
answered with the transaction. Each connection is synced with a ping
after its handshake, as Core's `TestNode.add_p2p_connection` does, so
the node has processed this peer's own `verack` before any transaction
is broadcast or the mock clock moves. Each subject starts its own node
rather than sharing one across the module: `mempool_sequence` is a
counter over a node's whole lifetime, and `pytest-randomly` does not
hold that ordering against a shared node still. The `btclib-node` cells
skip on `Capability.CLOCK`, the first capability each subject asks for
on either node.

`feature_utxo_set_hash.py`'s row computes the UTXO set's own
commitments independently, walking every block this harness's own chain
holds back off `getblock`, rather than trusting Core's own Python
reimplementation of the same arithmetic the way Core's own file does:
MuHash with `btclib.coinstats.CoinStats`, and `hash_serialized_3` as the
SHA256d Core's `kernel/coinstats.cpp` takes over the same `TxOutSer`
bytes, in its coins-view cursor's own order. Kept is that both agree
with `gettxoutsetinfo` over a chain carrying a coinbase-only run and one
spend; dropped is Core's own hard-coded `hash_serialized_3`/`muhash`
literals, deterministic only on Core's own exact chain. The row is one body
run against both nodes, and a `main` declaring `Capability.MINE` fails
it: its MuHash agrees, and `gettxoutsetinfo` then refuses
`hash_serialized_3`, Core's own default `hash_type`
([ISS btclib-node#1387](https://github.com/btclib-org/btclib-node/issues/1387)).

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

`rpc_getdescriptoractivity.py`'s own rows and `rpc_getblockstats.py`'s
own row are new capabilities rather than options:
`Capability.DESCRIPTOR_ACTIVITY` and `Capability.BLOCK_STATS`
(`capability.py`) name the RPC itself, `getdescriptoractivity` and
`getblockstats` naming no callback in `btclib-node`'s own dispatch
table on either build -- measured live, both answer "Method not found"
there. The `rpc_getblockstats.py` cell abbreviates its capability to
`(stats)` and the `rpc_getdescriptoractivity.py` cells name none, so
this paragraph is where both names are spelled out.
`rpc_getdescriptoractivity.py`'s own first row needs no `MiniWallet`,
and is what runs on bitcoind directly; its `(mempool)` row folds
together every one of Core's own subtests that needs `Capability.MINE`
on top of the RPC itself. `rpc_getdescriptoractivity.py` drops none of
Core's own subtests: kept is that an unused address carries no activity;
that a payment to a key-path p2tr output confirmed in a named block
makes `activity` the answer's only key and reports one `receive` entry,
checked for its `type`, `blockhash`, `height`, `txid`, `vout` and
`amount` and for its `output_spk`'s `hex`, `address`, `type`, the
witness version opening its `asm` and the `rawtr` function opening its
`desc`; that an unconfirmed payment is excluded when `include_mempool`
is `False`; its RPC-argument errors for a bad blockhash, a bad
descriptor and a missing argument; and Core's own multiple-address
query, its mix of a confirmed and an unconfirmed payment, its
receive-then-spend, and its no-address case, a coin paying
`mini_wallet.py`'s `RAW_P2PK_SCRIPT_PUB_KEY` spent under
`raw_p2pk_script_sig`
([ISS 167](https://github.com/btclib-org/bitcoin-node-tests/issues/167)).
`rpc_getblockstats.py`'s own kept and dropped set: kept is the genesis
block's own statistics --
independently computed as its serialized `TxOut` plus `getblockstats`'s
own per-coin overhead, the one the running build's `getnetworkinfo`
`version` implies, rather than copied from Core's own literals, genesis
being a network constant this harness's own chain shares with Core's --
and the same answer when the
block is selected by hash; that an `OP_RETURN` output is counted in
`utxo_increase`/`utxo_size_inc` but excluded from
`utxo_increase_actual`/`utxo_size_inc_actual`; that `stats=[...]`
narrows the answer; its height error messages; its statistic-name error
message wherever the invalid name sits in the list, and naming the name
given rather than a fixed one; mainnet's genesis hash answering "Block
not found"; its required-argument usage string; and a `blk00000.dat`
renamed away answering "Block not found on disk". Dropped is Core's own
vendored fixture and every comparison it feeds -- the full key set, the
heights and each statistic of the blocks it replays, by height and by
hash -- its per-stat query loop over those blocks, and its
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

Every `btclib-node` cell of this batch is a counted skip on the released
build. Neither `-fastprune` nor `-blockfilterindex` is one of `cli.py`'s
registered flags, on the released build or on `main`, and neither
build answers `scanblocks`. `Capability.INBOUND_EVICTION` is declared
per instance, by `btclib_node.py`'s own `_evicts_inbound` probe: the
released build carries no inbound eviction and skips on it, and a
`main` past
[ISS btclib-node#1064](https://github.com/btclib-org/btclib-node/issues/1064)
declares it and asks for `Capability.MINE` next, which a `main` from
the commit closing
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
on declares too. There the row is one body run against both nodes
(`tests/integration/conftest.py`'s own module docstring). A build before
[ISS btclib-node#1179](https://github.com/btclib-org/btclib-node/issues/1179)
fails it: a block a peer announces by `headers` is asked of peers that
connected before it rather than of the one that announced it, so that
peer never sees the `getdata` it waits for. A build past it passes.

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

bitcoind declares `TYPED_OUTBOUND` on regtest alone, `addconnection`
refusing any other chain (`src/rpc/net.cpp`). `btclib-node` declares
it on no build: `rpc/callbacks.py`'s dispatch table names no
`addconnection` on the released build or on `main`, `btclib_node.py`'s
own docstring naming the commits read. On `main`, `addnode` is the one
RPC that dials, and `_connection_type` reports what it opens as
`manual`.

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
without `-txreconciliation` ask for none of these. bitcoind starts with
`-debug=txreconciliation` besides, the category the registered and forgotten
peers' lines are written under.

`btclib-node`'s cell on the first `p2p_initial_headers_sync.py` row is a
disagreement on each build, and
`tests/integration/p2p_initial_headers_sync_btclib_node_test.py`'s own
docstring has both. On `p2p_sendtxrcncl.py` (off) it passes, and every
other row these files add is a counted skip.

`p2p_feefilter.py` is ported on it too, each of Core's checks a body over
fresh nodes in `tests/integration/p2p_feefilter_test.py`, whose module
docstring has what differs from Core's file. Its block-relay-only check
asks for `TYPED_OUTBOUND` and its `-blocksonly` check for `BLOCKS_ONLY`.
Its filtering check funds its transactions from a `MiniWallet` on a
second node, relayed to the node under test, so it asks for `MINE` of
both nodes and `CONNECT` of the second. The `forcerelay` check's
`-whitelist` asks for no capability, as the `noban` checks' do not, so
`btclib-node` meets
[ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)
there on each build. `btclib-node`'s other cells are a pass on `p2p_feefilter.py`'s
own row on each build; on the filtering row, a counted skip on a build
before
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
and a pass on one past it; and a counted skip on the block-relay-only
and `-blocksonly` rows.

`p2p_mutated_blocks.py` is ported on it too, each of Core's checks a
wire half and a log half over a fresh node in
`tests/integration/p2p_mutated_blocks_test.py`, whose module docstring
has what differs from Core's file. The mutated-block check has the node
dial an outbound full-relay peer, so it asks for `TYPED_OUTBOUND`, and
`MINE` for the block it announces, which spends a `MiniWallet` coin; the
missing-parent check's wire half asks for `MINE` alone. Each log half asks
for `DEBUG_LOG` besides, and the missing-parent one for
`TEST_ACTIVATION_HEIGHT` too. Its pin is past the pinned release:
Core's file there sends a `sendcmpct` and the block's header ahead of the
`cmpctblock`, where the release's own sends neither, and each `bitcoind`
cell is one verdict for both builds. `btclib-node`'s cell on the
missing-parent wire row is a counted skip on a build before
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
and a pass on one past it, and every other row this file adds is a
counted skip.

`feature_anchors.py` is ported on it too, each of Core's checks a body
over a fresh node in `tests/integration/feature_anchors_test.py`,
whose module docstring has what differs from Core's file. Its first check
has the node dial block-relay-only peers beside inbound ones, and reads
`anchors.dat` once the node stops; its second has the node dial a Tor v3
address through a `Socks5Proxy` given as `-onion`, so it asks for `PROXY`
besides. Each asks for `TYPED_OUTBOUND` and `DEBUG_LOG`, Core's own log
lines being where the node's read of the file, and in the second its
dump, are asserted. `btclib-node`'s cell on each is a counted skip on
`TYPED_OUTBOUND`.

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
asserts, on an older build, that the onion address is left out.
`btclib-node`'s cell on each row is a counted skip.

`p2p_ibd_stalling.py` is ported on it too, each of Core's checks a wire
half and a log half over a fresh node in
`tests/integration/p2p_ibd_stalling_test.py`, whose module docstring has
what differs from Core's file. Each body asks for `TYPED_OUTBOUND`, and
`CLOCK` for Core's own mock time; each log half asks for `DEBUG_LOG`
besides. Its `manual` check is read per-build, as
`p2p_add_connections.py`'s is: where the build's own `help addconnection`
names no `manual`, it asserts the refusal instead.
`btclib-node`'s cell on each row is a counted skip.

`p2p_tx_download.py` is ported on it too, each of Core's checks a body
over a fresh node in `tests/integration/p2p_tx_download_test.py`, whose
module docstring has what differs from Core's file. Every body asks for
`MINE`, to leave initial block download, and every body moving Core's own
mock time for `CLOCK`; the tiebreak and outbound checks ask for
`TYPED_OUTBOUND`, the inv-block check for `CONNECT`, the rejection check
for `MAXMEMPOOL` and the duplicate check for `DEBUG_LOG` besides. A peer
announcing by txid is `Peer.handshake`'s `wtxidrelay` off, Core's
`P2PInterface(wtxidrelay=False)`. Its `-whitelist` asks for no
capability, as the `noban` checks above do not.
The duplicate check is read per-build: the entries of one `inv` naming
the same transaction are processed once only on a build carrying
bitcoin/bitcoin@1278a5970d5ada0979052a5bad899e896b8ab40b, which the
pinned release does not, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, that each is
processed.

`btclib-node`'s cell on the spurious-`notfound` row is a counted skip on a
build before
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071)
and a pass on one past it; on the disconnect and `notfound` rows a counted
skip before it and a fail on
[ISS btclib-node#1196](https://github.com/btclib-org/btclib-node/issues/1196)
past it, and on the large-inv row a counted skip before it and a fail on
[ISS btclib-node#1320](https://github.com/btclib-org/btclib-node/issues/1320)
past it; every other row this file adds is a counted skip. A build that
asks every announcer at once
([ISS btclib-node#1196](https://github.com/btclib-org/btclib-node/issues/1196))
asks both peers of the disconnect and `notfound` checks for the
transaction, and Core's check that one alone is asked reads the counts
once one has been: it fails where the second request arrives before that
read, which on `node-integration.yml`'s runners it usually does, and
passes where it arrives after, a run
`.github/scripts/btclib_node_verdict.py` then reports as **fixed**.

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
and the same-txid check for `DEBUG_LOG` besides,
reading a line bitcoind writes under the `-debug=mempoolrej` it starts
with. The parent-confirmed check is read per-build: an orphan is taken
into the mempool once a block confirms its parent only on a build
carrying bitcoin/bitcoin@9cc7dc50bdc9867d079ab7a111d39487a4566767, which
the pinned release does not, so the body reads the build's own
`getnetworkinfo` `version` and asserts, on an older build, that the
orphan is kept. A transaction with no witness spends
`mini_wallet.py`'s `RAW_P2PK_SCRIPT_PUB_KEY`, Core's own `RAW_P2PK`
output, under `raw_p2pk_script_sig`, from coinbases the body mines.
`btclib-node`'s cell on each row is a counted skip on `ORPHANAGE`.

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

`btclib-node`'s cell on each log row is a counted skip, on the
outbound-`sendcmpct` and parallel-reconstruction rows a counted skip on
`TYPED_OUTBOUND`, and on each other row asking for `MINE` a counted skip
on a build before
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071).
Past it, each row fails where it first asks for what Core's node does and
that one does not: announcing a new block as a `cmpctblock`, or
reporting in `getpeerinfo` a peer asking for that
([ISS btclib-node#1223](https://github.com/btclib-org/btclib-node/issues/1223));
asking for a block as a compact one, taking a `cmpctblock`, or selecting a
peer for high-bandwidth mode
([ISS btclib-node#1321](https://github.com/btclib-org/btclib-node/issues/1321));
answering a `getblocktxn` for a block past Core's
`MAX_BLOCKTXN_DEPTH` with the whole block ahead of the `pong` of a `ping`
sent after it, the block arriving after that `pong`
([ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410));
and answering `getchaintips`
([ISS btclib-node#1393](https://github.com/btclib-org/btclib-node/issues/1393)).
The invalid-`sendcmpct` and empty-`getblocktxn` wire rows fail on every
build, the node keeping a peer Core's `master` drops
([ISS btclib-node#1451](https://github.com/btclib-org/btclib-node/issues/1451) and
[ISS btclib-node#1450](https://github.com/btclib-org/btclib-node/issues/1450)).

`p2p_opportunistic_1p1c.py` is ported on it, its rows above each
one of Core's checks as a body over a fresh node in
`tests/integration/p2p_opportunistic_1p1c_test.py`, whose module
docstring has what differs from Core's file. Every body asks for
`ORPHANAGE` first, and for `MAXMEMPOOL` and `MINE`: its node restarts
with the `-maxmempool` Core's own starts with, and
`mempool_util.fill_mempool` fills its mempool. The parent-first,
low-and-high-child, multiple-parents and parent-in-mempool checks have
the node dial outbound full-relay peers, so they ask for
`TYPED_OUTBOUND`, and every check but the one chaining a package on
another asks for `CLOCK`. A `P2PK` row is its check over a parent with
no witness, Core's `RAW_P2PK` wallet. Each `bitcoind` cell is one
verdict for the pinned release and for Core's `master`. `btclib-node`'s
cell on each row is a counted skip on `ORPHANAGE`
([ISS btclib-node#1420](https://github.com/btclib-org/btclib-node/issues/1420)).
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

[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47): a
test listens as a SOCKS5 proxy, points the node at it, and reads what
the node asked for. `socks5.Socks5Proxy` is that proxy, bound to loopback
and accepting on a thread of its own. It answers each `CONNECT` with
success and queues a `Socks5Request` -- the address type, the host, the
port and any RFC 1929 credentials -- for `next_request`, then holds the
connection open until `close`, as Core's own `Socks5Server` does only
under its `keep_alive` setting. The node keeps the peer, and
`getpeerinfo` lists it, until `close` or until the node's own
`-peertimeout` drops a peer that never answered. Given a
`destinations_factory`, as Core's own server is, it forwards each
connection where the factory names instead, or closes it where the
factory names nowhere.
`socks5_test.py` drives it against a client written octet by octet.
It listens on IPv4 loopback, or on IPv6 loopback or a unix socket where
its `family` asks, and `endpoint` spells each the way `-proxy` takes it.
`Capability.PROXY` is what a test asks for: `-proxy`, with its
`=<network>` suffix and a `unix:` path, `-onion` and `-proxyrandomize`,
bitcoind's own flags. `Capability.CJDNS`, `Capability.I2P_SAM` and
`Capability.ONLYNET` are `-cjdnsreachable`, `-i2psam` and `-onlynet`.
`btclib-node` declares none of them on any build, `cli.py` registering
none of those flags (`btclib_node.py`'s own docstring names the commits
read).

`feature_proxy.py` is ported on it, its rows above. Each of Core's
nodes is a test of its own; every start Core's file expects refused is
refused with Core's own wording whole; and the starts giving `-proxy` a
network suffix compare every network's proxy, where Core's file reads
only the networks each start names.
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

`p2p_private_broadcast_cap.py` is not ported: the file is past the
pinned release, whose binary puts no cap on its private broadcast queue,
the file's whole subject, and the `-proxy` its node is given names a
port nothing listens at, so it needs no listening proxy.
`p2p_private_broadcast_retry_v1.py` is not ported either: in Core's
file, the peers its node reaches over IPv4 through the Tor proxy, all but
the one whose transport it reads, answer in BIP324's v2 transport, which
`Peer` does not speak.
The rest of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47) is
`p2p_private_broadcast_retry_v1.py` and the proxy steps of
`feature_config_args.py` and `rpc_net.py`, which ISS 14's list above
holds for their log steps.

## The node wallet: `Capability.NODE_WALLET`

[ISS 45](https://github.com/btclib-org/bitcoin-node-tests/issues/45)
holds Core's tests whose subject is bitcoind's own wallet, every
`wallet_*.py` file of Core's `test/functional/` among them. A port of one
that reaches the wallet runs one body over both nodes, each wallet step
behind `Capability.NODE_WALLET` (`capability.py`). `BitcoindAdapter` declares
it wherever its build carries the wallet, `_has_wallet` (`bitcoind.py`)
being the probe it shares with `Capability.MINE`, and no other adapter
declares it.
btclib-node keeps no wallet: `rpc/callbacks.py`'s dispatch table names no
wallet RPC on the released build or on `main` (`d2b4efa5`), so each
such port's `btclib-node` cell is a counted skip on it until
[ISS 199](https://github.com/btclib-org/bitcoin-node-tests/issues/199)
gives the btclib side a wallet to reach.

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
`Capability.GENERATE`, `Capability.INVALIDATE_BLOCK`, `Capability.CLOCK`
and `Capability.MINE`, and its file is the same at the pinned release.
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
