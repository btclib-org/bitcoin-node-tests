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
