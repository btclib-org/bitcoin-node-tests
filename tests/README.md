# Tests and code coverage

## The suite

```shell
uv sync
uv run pytest
```

`--cov` is in `addopts`, so the bare `pytest` is the coverage gate, the
same measurement the `coverage` job makes, and it answers against
`fail_under` in `pyproject.toml`. A run that selects a subset — a path
that leaves part of the suite behind, `-k`, `-m`, `--deselect`,
`--ignore`, `--ignore-glob` or `--lf` — prints the report without the
threshold: `coverage_fail_under` in `tests/conftest.py` is where that
happens, and section 8 of [the organization standard][std] names the
set.

```shell
uv run pytest --no-cov
```

runs the suite without measuring anything.

## The integration layer

`tests/integration/` reaches a real node -- a process, an RPC socket, a
p2p socket -- and skips itself without `TF2_INTEGRATION=1` in the
environment, `tests/integration/conftest.py`'s own module docstring
naming the rest of the switches.

```shell
TF2_INTEGRATION=1 uv run pytest tests/integration
```

Its bodies are `[tool.coverage.run]`'s own `omit`: an ordinary run never
executes them, so the ratchet would otherwise measure the switch rather
than this package, the same reasoning btclib's own `pyproject.toml`
carries for its own `tests/integration/*`.

## Convention tests

Section 7 of [the organization standard][std] lists conventions a suite
can turn into a red test, and a repository needs the ones its own prose
states rather than all of them. So which of them this repository tests
is declared here, in two halves that together account for every one of
them: the table below and the "Not tested here" line under it.

This step of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220)
carries the organization's apparatus, the ledger, and step 3's own
adapter -- `bitcoind`, `btclib_node`, `capability`, `node`, `peer` -- with
real public functions of its own; the test families of later steps are
what this step still leaves untested rather than what this step lacks
to test.

| convention | tested in |
| --- | --- |
| the public surface | `all_test.py` |
| the copyright header | `copyright_test.py` |
| the documentation | `docs_test.py` |
| the changelog | `changelog_test.py` |

The build system is a convention this tree holds regardless of tier --
`[build-system]` declares `uv_build`, and `pyroma` and `check-sdist` are
owed and run as local hooks, section 4's condition being a declared
backend and not a release -- and nothing in `tests/` checks it a second
way, that gate being the lint gate's and not a pytest one.

The import graph, the calling convention and input validation are each a
generic walk over the public surface, and this step does not build one:
`node_test.py`, `bitcoind_test.py`, `btclib_node_test.py` and
`peer_test.py` hold each function to what it does by hand rather than to
a rule a walk would enforce over every one of them at once, which is
what a repository electing one of these conventions buys over the
per-function tests this step already has.

**The suite opens no socket** is the one of the three that this
package's own subject makes an odd fit rather than merely an unbuilt
walk: rule 1 of ISS 2220 is that reaching a node is a socket, so a
generic check for "every construction that could reach the network
carries the argument that keeps it hermetic" would have to tell
`peer_test.py`'s own loopback-bound `_FakeNode` -- hermetic by
construction, and the only socket the unit suite opens -- from
`tests/integration/`'s deliberately real one, gated instead by
`TF2_INTEGRATION` and left out of the coverage ratchet by
`[tool.coverage.run]`'s own `omit`. Building that distinction is a
bigger investment than this step owes for a package whose whole point is
the socket the convention would otherwise forbid.

Not tested here: the import graph; the build system; the calling
convention; input validation; the suite opens no socket.

## The ledger

`TF2.md` is the record of what Bitcoin Core's
`test/functional/test_framework/` needs and what covers it, rebuilt here
from [ISS 2220](https://github.com/btclib-org/btclib/issues/2220) now
that tf2 has a repository of its own. `tf2_ledger_test.py` holds it to a
transcription of Core's directory; `.github/workflows/vendored-vectors.yml`
re-checks every pin weekly and a separate job re-reads the directory
itself, so a file Core gains is a finding distinct from a pin gone stale.

[std]: https://github.com/btclib-org/.github/blob/main/README.md
