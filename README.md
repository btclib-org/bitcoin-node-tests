# bitcoin-node-tests

Bitcoin Core's functional test suite, rewritten on
[btclib](https://github.com/btclib-org/btclib), as a non-regression
suite for any node that speaks bitcoin's RPC and p2p -- its own
repository rather than a feature of one node's own test suite, so that
it can sit beside, or replace, Core's own `test/functional/test_framework/`
(issue btclib-org/btclib#2220). tf2 is this project's nickname and its
label.

<!-- The badges are what the reader decides with, in three groups: what the
software is and whether it can be used, whether it works, and what the
OpenSSF makes of it. This tree publishes nothing yet (issue
btclib-org/btclib#2220), so the first group and the licence badge, both
tier 1's, are absent.
-->
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/btclib-org/bitcoin-node-tests/main.svg)](https://results.pre-commit.ci/latest/github/btclib-org/bitcoin-node-tests/main)
[![lint workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/lint.yml?query=branch%3Amain)
[![test workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/test.yml?query=branch%3Amain)
[![docs workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/docs.yml?query=branch%3Amain)
[![vendored-vectors workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/vendored-vectors.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/vendored-vectors.yml?query=branch%3Amain)
[![links workflow status](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/btclib-org/bitcoin-node-tests/actions/workflows/links.yml?query=branch%3Amain)

The ambition is a suite for every full node speaking that protocol:
today [Bitcoin Core](https://github.com/bitcoin/bitcoin) and
[btclib-node](https://github.com/btclib-org/btclib-node), tomorrow
whichever other implementation gains an adapter -- a `NodeAdapter`
subclass declaring what it can do
(`src/bitcoin_node_tests/node.py`), the way `bitcoind.py` and
`btclib_node.py` already do. A test passes on `bitcoind` before its
failure on any other node counts as a finding, filed on that node's own
tracker.

It imports [btclib](https://github.com/btclib-org/btclib) and
[bitcoin-core-rpc](https://github.com/btclib-org/bitcoin-core-rpc). It
imports no node: what it needs from one, it gets over a socket -- a
process, an RPC connection, a p2p connection.

`TF2.md` is the ledger of what Core's `test/functional/test_framework/`
needs and what covers it, one entry per file, each pinned to the
revision it was read at.

## Running it against your own tree

The suite is meant to be run by the people who change a node: a Bitcoin
Core developer against their own `master`, a btclib-node developer
against their own `main`, each a clone beside this one -- for instance
all three under one `upstream/` folder.

This repository publishes nothing yet (issue btclib-org/btclib#2220):
`git clone` and `uv sync` is how a checkout gets an environment, uv
being the only tool that has to be installed.

The unit suite reaches no network and starts no node.
`tests/integration/` does, against a node a checkout of your own
provides -- a `bitcoind` built from a Bitcoin Core checkout, or an
interpreter `btclib-node` is installed into -- and skips cleanly without
one. [CONTRIBUTING.md](./CONTRIBUTING.md)'s *The environment and the
gates* has the commands for both.

A test's skip names a capability the node it ran against does not
declare, and the run prints one count per capability rather than
passing in silence.

## CI

`node-integration.yml`'s `bitcoind` job is a required check: it installs
the pinned Bitcoin Core release under test and fails the run if the
tests it starts do not run. Its `btclib-node` job runs the same suite
from PyPI and reports without gating, a disagreement there being a
finding on that node's own tracker rather than a defect of this
repository's gates. The pinned release stays the only required oracle:
jobs running the suite against a Bitcoin Core `master` build and against
btclib-node's `main` are decided in
[ISS 8](https://github.com/btclib-org/bitcoin-node-tests/issues/8), and
report without gating.

## Contributing

[CONTRIBUTING.md](./CONTRIBUTING.md) has the commands each CI job runs,
verbatim. [REVIEWING.md](./REVIEWING.md) is what a pull request is
answered against. How the organization decides, and who holds which
role, is its
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
