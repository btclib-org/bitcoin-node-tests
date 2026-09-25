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

## Convention tests

Section 7 of [the organization standard][std] lists conventions a suite
can turn into a red test, and a repository needs the ones its own prose
states rather than all of them. So which of them this repository tests
is declared here, in two halves that together account for every one of
them: the table below and the "Not tested here" line under it.

This step of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220)
carries the organization's apparatus, the ledger, and one package module
that publishes nothing; the adapter and the test families of later steps
bring the conventions this step declares untested.

| convention | tested in |
| --- | --- |
| the public surface | `all_test.py` |
| the copyright header | `copyright_test.py` |
| the documentation | `docs_test.py` |
| the changelog | `changelog_test.py` |

This step ships one module, the package root, with an empty `__all__`
and no public function: the import graph has nothing to cycle in, the
calling convention and input validation have no function to hold one,
and nothing here opens a socket. The build system is a convention this
tree holds regardless of tier -- `[build-system]` declares `uv_build`,
and `pyroma` and `check-sdist` are owed and run as local hooks, section
4's condition being a declared backend and not a release -- and nothing
in `tests/` checks it a second way, that gate being the lint gate's and
not a pytest one.

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
