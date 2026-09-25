# bitcoin-node-tests

Bitcoin Core's functional test suite, rewritten on
[btclib](https://github.com/btclib-org/btclib), run against any node
that speaks bitcoin's RPC and p2p. tf2 is this project's nickname and
its label.

<!-- The badges are what the reader decides with, in three groups: what the
software is and whether it can be used, whether it works, and what the
OpenSSF makes of it. This tree publishes nothing yet (issue
btclib-org/btclib#2220, step 2 of 5), so the first group and the licence
badge, both tier 1's, are absent.
-->
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/btclib-org/bitcoin-node-tests/main.svg)](https://results.pre-commit.ci/latest/github/btclib-org/bitcoin-node-tests/main)
[![lint workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/lint.yml?query=branch%3Amain)
[![test workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/test.yml?query=branch%3Amain)
[![docs workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/docs.yml?query=branch%3Amain)
[![vendored-vectors workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/vendored-vectors.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/vendored-vectors.yml?query=branch%3Amain)
[![links workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/links.yml?query=branch%3Amain)

Two objectives, in this order: every Core test that tests a node runs
against [btclib-node](https://github.com/btclib-org/btclib-node), and
Core gets a typed, covered suite it can run against `bitcoind`. A test
passes on `bitcoind` before its failure on any other node counts as a
finding, filed on that node's own tracker.

It imports [btclib](https://github.com/btclib-org/btclib) and
[bitcoin-core-rpc](https://github.com/btclib-org/bitcoin-core-rpc). It
imports no node: what it needs from one, it gets over a socket -- a
process, an RPC connection, a p2p connection.

`TF2.md` is the ledger of what Core's `test/functional/test_framework/`
needs and what covers it, one entry per file, each pinned to the
revision it was read at.

## Installing

Nothing to install yet: this repository carries the organization's
apparatus and the ledger (issue btclib-org/btclib#2220, step 2 of 5).
The adapter and the test families are later steps of that same issue.

## Contributing

[CONTRIBUTING.md](./CONTRIBUTING.md) has the commands each CI job runs,
verbatim. `uv sync` creates the environment; uv is the only tool that has to be
installed. [REVIEWING.md](./REVIEWING.md) is what a pull request is answered
against. How the organization decides, and who holds which role, is its
[GOVERNANCE.md](https://github.com/btclib-org/.github/blob/main/GOVERNANCE.md);
what it intends to do, and what it deliberately does not, is its
[ROADMAP.md](https://github.com/btclib-org/.github/blob/main/ROADMAP.md).

## Links

- Source: <https://github.com/btclib-org/bitcoin-node-tests>
- [CHANGELOG.md](./CHANGELOG.md)

<!-- No "actively supported by" line: section 2 of the organization
standard gives it to a tier-1 tree, an index rendering the README with
no organization beside it -- this tree publishes nothing yet, and
below tier 1 `profile/README.md` says it once for all. -->
