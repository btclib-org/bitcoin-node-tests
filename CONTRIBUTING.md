# Contributing

What this repository holds in common with the others of the organization
— the toolchain, the lint gate, the tool tables behind it, the workflow
set and the branch rules — is stated once in the
[btclib-org repository standard](https://github.com/btclib-org/.github),
each rule with the alternative it was decided against. It binds this
repository, so a change departing from it is a divergence, and one filed
as an issue in that repository rather than here: a difference between two
repositories belongs to neither of them.

**This file is the same in every repository of the organization up to
its last section.** What is true of one tree only — the commands that
build its environment, the gates it runs, which of its workflows decide
a merge — is under that heading, and the comparison stops there.

How the organization decides, and who holds which role, is
[`GOVERNANCE.md`][governance]; what it intends to do, and what it
deliberately does not, is [`ROADMAP.md`][roadmap]. Both are the
organization's, one copy each beside the standard.

## The issue tracker

Where an issue is filed, and what an alignment finding has to name, is
[the standard's *What this repository is*][s-what]: an issue spanning
repositories, or whose subject is the standard, goes to
[btclib-org/.github](https://github.com/btclib-org/.github/issues), and
one about this tree alone stays here.

A finding noticed while doing something else goes where `REVIEWING.md`'s
*What is filed, and what is not* says, for an author as much as for a
reviewer: a pull request answering two questions cannot be accepted for
either.

## Documentation and comments

[Section 9 of the standard][s9] is the prose style, and it governs the
prose this tree ships — comments, docstrings and markdown. It is not
restated here: a second wording is the one that goes stale, which is
that section's own *One fact in one place*.

A commit message is prose this tree ships too, though section 9 does not
say so: [the only merge method the rule accepts][s11] puts it on `main`
as the landing commit's body, so what is written in one is read there
long after the branch is gone.

## Pull requests

What `main` accepts, and what it refuses to everyone, is [section 11 of
the standard][s11]. Run the gates locally before opening anything —
the last section of this file says which they are — because CI runs
exactly them, so a red run there is a local run that was not done.

What a pull request's title and description have to say about the issues
it closes, and why a manual link in the Development panel is a trap
neither of them shows, is [the standard's *What a pull request says it
is*][s-title]. Read it before opening one; it is the rule most often
found broken after the fact.

**Before it is opened, the branch's own commit subjects and bodies are
read against that same rule.** The description does not exist yet to
disagree with them, and [the standard][s-title] has the command that
scans the branch's own commit text for a verb in front of a reference.

**The two spellings are named here as well as there, against [section 9's
*One fact in one place*][s9]**, the paragraph above naming the section
and not the forms, which are the half a citation is got wrong in:
`(closes #N)` cites an issue the change closes, wherever the citation
sits — the title, the commit subject where [*Merge method*][s11] makes
that the thing that lands, and a `CHANGELOG.md` entry — and `(issue #N)`
cites, in those same places, an issue the change advances and does *not*
close. One token holds one meaning whichever file it sits in, so the
pair is chosen by what is true of the change rather than by which file
is being written, and a tree's own landed subjects are not what to copy
it from: nothing already landed is rewritten, so what a repository wrote
before the rule stays where it is.

`REVIEWING.md` is the standard a review is written against, and is this
file's other half. Read before opening a pull request, it is what the
pull request will be answered against.

`CHANGELOG.md` gets an entry for anything a reader would notice, and the
release notes move only for something a user has to *act* on, in the
repositories that publish.

Where that entry goes is [section 9][s9]'s — the end of the open
section — and no gate reads it: `check-changelog` is handed the file and
no base, so it cannot tell which entry the branch wrote. The open
section's headings, in the order the file holds them, a branch's own
last:

```shell
awk '/^## /{n++} n==1 && /^### /' CHANGELOG.md
```

`n==1` takes the open section, from the first `##` heading to the next,
and the scan is `/^## /` rather than `/^## v/`: a section headed
`## Unreleased` is no match for `/^## v/`, which counts from the first
release heading instead and prints a released section's entries — or
nothing, where the tree has released nothing — while reading as a
check that passed.

### One subject, opened as soon as it is written

A pull request answers one question. Issues that share a subject are one
pull request, closing each of them; issues that do not are one pull
request each, however small either of them is.

It is opened the moment it is written and verified — not held for the
previous one to be reviewed or to land, and not batched with the next. A
batch arrives as one reviewing job with several subjects, which is the
shape that costs the most to read; a finished pull request held back is
review that could have started and did not.

Working this way stacks branches, which is fine and costs one rule: a
child whose base was amended is moved with the old base named,

```shell
git rebase --onto <new-base> <old-base-sha> <child>
```

because a plain rebase replays the base's old commit inside the child,
and the forge then shows the base's old text as additions with nothing
red anywhere. Read the child's diff afterwards rather than trusting the
rebase, and retarget each child onto `main` as its parent lands.

### The landing queue

Where more than one pull request is open against this repository, only
one is carried to `main` at a time: rebased onto the tip, reviewed on
that head, and landed, while every other one waits, untouched, for its
turn. This governs which of several *already open* pull requests reaches
`main` next; *One subject, opened as soon as it is written* above governs
the moment before that, when a finished one is opened — the two do not
conflict, since a pull request is still opened without delay and still
waits its turn once several are open.

The reason is CI throughput, not the ack a waiting pull request keeps —
`REVIEWING.md`'s *The verdict* states what an ack belongs to, and
*Landing it* below states which rebase voids one. Every rebase queues
this repository's whole check matrix against the organization's ceiling
on concurrent jobs, so rebasing every waiting pull request after each
landing spends that capacity on runs the next landing invalidates
anyway, and delays the one pull request that is actually next: work
spent on a pull request that is not next is work that delays the one
that is. The ceiling's figure is `REPOSITORY.md`'s, under *Plan-gated
settings*, beside the command that re-derives it.

Order is cheapest and least contended first, most invasive last, so that
a large change does not sit at the head blocking everything behind it.

The maintainer may declare a bounded exception — several pull requests in
flight against one repository, for a named piece of work — trading the
cost above for throughput; it is recorded as a comment in
[btclib-org/.github](https://github.com/btclib-org/.github/issues), by
*The issue tracker* above, and holds only for the work it names.

### The review

A review is given promptly and on local evidence. It does not wait for
CI, does not report a check as a finding, and does not discuss a run at
all: whether CI is green is the author's business, once, at landing time.

The exchange is anchored to a sha rather than to a branch, a branch being
free to move under a review:

- the author hands off by naming the sha pushed and the evidence run
  against it, then leaves that head alone;
- the reviewer answers with findings — where, what is wrong, how they
  know it, and whether each is blocking;
- the author accepts what is reasonable, declines the rest with a reason
  in the thread, and pushes the answer without waiting for CI;
- the reviewer resolves the threads they opened, that being what says a
  finding is closed, and re-reviews the delta rather than the branch.

**What ends the loop is the ack of record**, and the author does not
supply their own. A reading that says what it found and delivers no
verdict is a review too and ends nothing; [the standard's *Review*][s-rev]
has which is which, and `REVIEWING.md` has how each is written. A
disagreement that survives a second exchange goes to the maintainer
instead of into a third round.

### Landing it

CI is read once, and this is where. Rebase onto `main`'s tip, push that
head so the checks run on the tree that will land, and only then wait for
them: checks read before a rebase describe a tree nobody is landing. A
rebase that moved nothing but the base leaves the ack standing; one that
resolved a conflict does not, that resolution being a change no reviewer
has seen.

Then squash, [the only method the rule accepts][s11].

**The maintainer's bypass is not automatic — it has to be invoked, and
`gh pr merge` cannot invoke it**, refusing client-side before it asks
GitHub anything:

```text
Pull request is not mergeable: the base branch policy prohibits the merge
```

The merge endpoint applies it server-side, and it is the same endpoint
the merge button asks:

```shell
gh api -X PUT repos/{owner}/{repo}/pulls/<n>/merge \
  -f merge_method=squash -f sha=<the head the checks ran on>
```

**The `sha` is not optional.** Reading the ack and merging are two
calls, and the head is free to move between them — the push that would
move it comes out of the same round the verdict does. Unpinned, the
command takes whatever sits at the head when it runs; pinned, [the
endpoint answers `409` where the head has moved][gh-merge], and a round
lost that way is cheaper than a tree nobody has read reaching `main`.
*The review* above anchors the exchange to a sha and [section 11][s11]
has an ack name one: the pin is that rule reaching the call that
performs the landing.

**Verify what landed rather than trusting the answer**, the signature
[the standard asks for][s-sigs] being a valid one rather than a
particular signer's:

```shell
gh api repos/{owner}/{repo}/commits/main \
  --jq '.commit.verification | {verified, reason}'
```

**What it closed is read again here too, from the landed sha rather
than from the pull request**: [the standard's *What a pull request says
it is*][s-title] has the second read, and why the first alone does not
reach a squash subject composed after it runs.

The forge deletes the head branch itself, per the setting section 11
names. What is still yours is bringing every checkout sitting on `main`
up to date,
that being where the next session starts from and a stale one being where
a branch gets built on a base that has moved. `REPOSITORY.md` carries the
settings and why they are what they are.

[s-what]: https://github.com/btclib-org/.github#what-this-repository-is
[s11]: https://github.com/btclib-org/.github#11-github-settings
[s9]: https://github.com/btclib-org/.github#9-prose-comments-and-docstrings
[s-title]: https://github.com/btclib-org/.github#what-a-pull-request-says-it-is
[s-rev]: https://github.com/btclib-org/.github#review
[s-sigs]: https://github.com/btclib-org/.github#signatures
[gh-merge]: https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request
[governance]: https://github.com/btclib-org/.github/blob/main/GOVERNANCE.md
[roadmap]: https://github.com/btclib-org/.github/blob/main/ROADMAP.md

## This repository in particular

Everything above is the same file in every repository of the
organization; everything below is this one's, and the comparison stops at
this heading.

<!-- The toolchain badges are here rather than in the README because they
report no state: each names a choice, and this is the file that says how
the choice is enforced and what the command for it is. The README keeps
the badges that can turn red, the same split some sibling repositories
of the organization use. --> [![calendar versioning:
yyyy.m.d](<https://img.shields.io/badge/cal_ver-yyyy.m.d-1674b1.svg?logo=calver>)](<https://calver.org/>)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![format:
ruff](https://img.shields.io/badge/format-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/formatter/)
[![lint:
ruff](https://img.shields.io/badge/lint-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/)
[![docstrings:
ruff](https://img.shields.io/badge/docstrings-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/rules/#pydocstyle-d)
[![type check:
mypy](https://img.shields.io/badge/type_check-mypy-yellowgreen.svg?logo=mypy)](https://mypy-lang.org/)
[![lint:
markdownlint-cli2](https://img.shields.io/badge/lint-markdownlint--cli2-yellowgreen.svg?logo=markdown)](https://github.com/DavidAnson/markdownlint-cli2)
[![pre-commit
enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub repository:
btclib-org/bitcoin-node-tests](https://img.shields.io/badge/GitHub-btclib--org%2Fbitcoin--node--tests-181717?logo=github)](https://github.com/btclib-org/bitcoin-node-tests/)

To get an overview of the project, read the [README](./README.md) and
[ISS 2220](https://github.com/btclib-org/btclib/issues/2220), the charter
this repository is step 2 of.

What a primitive does -- a curve operation, a signature scheme, a script
-- is btclib's, not this package's: a finding that reproduces with
`btclib` alone is an issue for
[its tracker](https://github.com/btclib-org/btclib/issues) rather than
this one, and a disagreement between two nodes is a finding on the
losing node's own tracker (rule 3 of issue btclib-org/btclib#2220), never
here.

### The one constraint

**This package is built on btclib and bitcoin-core-rpc, imports no node,
and reaches one only over a socket.** Rule 1 of
[ISS 2220](https://github.com/btclib-org/btclib/issues/2220). A test is
written in btclib's names, consensus constants keeping Core's spelling
and no alias layer (rule 2).

### The public surface

Step 3 of ISS 2220 is the adapter -- `bitcoind`, `btclib_node`,
`capability`, `node`, `peer` -- each its own submodule with its own
`__all__`; the test families of later steps are what adds to the tree
this rule already covers. The package root re-exports none of them and
keeps an empty `__all__` by decision, a caller importing the submodule
it needs instead. **Every module and every package declares `__all__`**,
at every depth of the tree, and `tests/all_test.py` is the census.

### The environment and the gates

uv is the only tool that must be installed; it fetches interpreters,
linters and packaging tools itself. `uv sync` creates the environment.

```shell
uv sync
```

The unit suite reaches no network and starts no node: `tests/integration/`
is the one part of the tree that does, gated on `TF2_INTEGRATION` and
skipping itself without it, matching the switch btclib's own
`tests/integration/` carries -- named `TF2_INTEGRATION` here rather than
`BTCLIB_INTEGRATION`, tf2 being this repository's own label.
`TF2_BITCOIND` and `TF2_BTCLIB_NODE_PYTHON` name the two nodes:
a `bitcoind` on `PATH` or named directly, and the interpreter
`btclib-node` is importable by -- never this project's own, kept
separate from it regardless of what `requires-python` names (issue
bitcoin-node-tests#42). Both skip cleanly, naming what to set, rather
than failing on a program this repository does not ship.

```shell
TF2_INTEGRATION=1 uv run pytest tests/integration
```

[tests/README.md](./tests/README.md) is where the suite and its
convention tests are described.

`TF2_BITCOIND` and `TF2_BTCLIB_NODE_PYTHON` name a node built or
installed from a checkout of the developer's own -- a Bitcoin Core
developer's `master`, a btclib-node developer's `main` -- commonly a
clone beside this one (`../bitcoin`, `../btclib-node`) rather than a
copy inside this tree.

A Bitcoin Core developer, against a `bitcoind` built from `master`
(Core's `src/CMakeLists.txt` sets `CMAKE_RUNTIME_OUTPUT_DIRECTORY` to
the build directory's `bin/`):

```shell
cmake -S ../bitcoin -B ../bitcoin/build
cmake --build ../bitcoin/build
TF2_INTEGRATION=1 \
    TF2_BITCOIND=../bitcoin/build/bin/bitcoind \
    uv run pytest tests/integration
```

A btclib-node developer, against their own checkout's own environment,
where `uv sync` installs `btclib-node` editable -- kept separate from
the interpreter running `pytest` regardless of version (issue
bitcoin-node-tests#42):

```shell
uv sync --project ../btclib-node
TF2_INTEGRATION=1 \
    TF2_BTCLIB_NODE_PYTHON=../btclib-node/.venv/bin/python \
    uv run pytest tests/integration
```

Both nodes at once run every test that needs one against both, a
disagreement between them being a finding rather than a failure of the
suite (rule 3 of
[ISS 2220](https://github.com/btclib-org/btclib/issues/2220)).

The gate is the suite, the hooks and the documentation build:

```shell
uv run pytest
uv run pre-commit run --all-files
uv run --locked --exact --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
```

`uv run pytest` above never reaches `tests/integration`'s own bodies:
`TF2_INTEGRATION` is unset, so each skips itself and `[tool.coverage.run]`'s
`omit` leaves the ratchet measuring what that run actually executed.

`--cov` is in `addopts`, so the bare `pytest` above is the coverage gate
and `fail_under` is what it answers against -- 100%, and coverage takes
that literally: a statement or a branch no test reaches fails it. A
selective run is reported and not gated, and `tests/conftest.py`'s
`coverage_fail_under` is what makes that difference.

The documentation build is the one to remember, because no hook reads
reStructuredText: a docstring docutils cannot parse fails it with every
hook green. `-n` turns an unresolved cross-reference into a warning for
`-W` to fail on, and `conf.py`'s `intersphinx_mapping` is what resolves a
reference into the standard library, btclib or bitcoin-core-rpc.

**`--exact` above is not optional.** `uv sync` (this section's first
command) installs `dev`, which carries `pytest`; `--no-default-groups
--group docs` alone only adds what `docs` needs to that same venv and
prunes nothing, so a module importing `pytest` builds locally with no
warning while CI's own job, a fresh venv per run, fails on it
(`CLAUDE.md`'s own note on this has the case that happened).

**Check exit codes, not filtered output.** `pre-commit run ... | grep -v
Passed` hides a failure, and `grep` finding nothing exits 1, which is not
the gate's answer to anything.

**The lint gate is not installed as a git hook.** `pre-commit install`
writes into the common git directory, which every worktree of this
repository shares: `git -C <worktree> rev-parse --git-path hooks` answers
with the primary checkout's `.git/hooks` from every one of them. So one
session installing it installs it for every other. Run the gate by hand
before committing -- the `uv run pre-commit run --all-files` above.

One of those hooks needs maintenance, and only one. `.secrets.baseline`
carries no reviewed finding yet -- this tree vendors no test vector and
no golden file -- but its two entropy plugins are off from the first
scan, the same way every other repository of the organization keeps
them off: a 40-character commit SHA is what most of `.pre-commit-config.yaml`'s
own `rev:` pins are, and a hex string that long is indistinguishable
from a high-entropy secret to a detector that does not know what a git
pin looks like. Adding a vector or a golden file later, or seeing a new
false positive from a legitimate high-entropy string, means
regenerating:

```shell
uvx --from detect-secrets detect-secrets scan \
    --disable-plugin Base64HighEntropyString \
    --disable-plugin HexHighEntropyString \
    --baseline .secrets.baseline
```

Read the resulting diff before committing it. That is the whole point of
a baseline rather than an exclusion: what appears in it is what nobody
has looked at yet, so regenerating without reading turns the review into
a formality.

### Running against a Core developer's own build

Issue [bitcoin-node-tests#36](https://github.com/btclib-org/bitcoin-node-tests/issues/36):
a Core developer runs this suite beside `test/functional`, or in place
of it, with the options `test_framework.py` and `test_runner.py` give
them.

**The interpreter.** `requires-python` is `>=3.12`, by the maintainer's
own decision departing from section 1 of the organization standard and
from btclib-org/.github#1324 -- `pyproject.toml`'s own comment on
`requires-python` has the measurement, `typing.override` and `sphinx`
both needing 3.12 and nothing here needing more. `uv run` fetches that
interpreter on its own where none is on `PATH`, whatever floor is
named: measured under `UV_PYTHON_PREFERENCE=only-managed` and a fresh
`UV_PYTHON_INSTALL_DIR`, with no matching interpreter visible anywhere
first, `uv run` downloaded the interpreter `.python-version` names and
ran on it. So a Core developer needs no interpreter of their own either
way; lowering the floor is what lets one who already has 3.12 or newer
skip that download.

**Options.** Core's own option is the row's key, every one either file
takes at Core's `master` or at the pinned `v31.1`; `--` is a cell this
suite has nothing under.

| Core's option | this suite's equivalent |
| --- | --- |
| `--nocleanup` | pytest's own `--basetemp=<dir>`; see below |
| `--cachedir` | -- (no pregenerated-datadir cache exists) |
| `--tmpdir` | pytest's own `--basetemp=<dir>` |
| `-l`, `--loglevel` | -- (no central logger to set a level on) |
| `--tracerpc` | `--tracerpc`, `tests/integration/conftest.py` |
| `--portseed` | -- (`node.free_port` asks the OS, never a seed) |
| `--previous-releases` | -- (no previous-release binaries mechanism) |
| `--coveragedir` | -- (no RPC-coverage instrumentation) |
| `--configfile` | belongs to issue bitcoin-node-tests#53 |
| `--pdbonfailure` | pytest's own `--pdb` |
| `--usecli` | -- (rule 1 reaches a node only over RPC) |
| `--valgrind` | through the adapter; see below |
| `--randomseed` | `pytest-randomly`'s own `--randomly-seed` |
| `--timeout-factor` | `--timeout-factor`, `tests/integration/conftest.py` |
| `--v2transport` | through the adapter; see below |
| `--v1transport` | through the adapter; see below |
| `--test_methods` | pytest's own node ids, or `-k` |
| `-f`, `--fff` | -- (Core's dummy argument for IPython) |
| `--perf` (`v31.1` only) | -- (a `TF2_BITCOIND` wrapper, as `--valgrind`) |
| `--ansi` | pytest's own `--color=yes\|no\|auto` |
| `--combinedlogslen`, `-c` | -- (no combined log; `--basetemp` names each) |
| `--coverage` | -- (paired with `--coveragedir` above) |
| `--exclude`, `-x` | pytest's own `--deselect`, `--ignore`, or `-k 'not ...'` |
| `--extended` | -- (every family runs; no extended/basic split) |
| `--help`, `-h`, `-?` | pytest's own `-h` |
| `--jobs`, `-j` | `pytest-xdist`'s own `-n` |
| `--keepcache`, `-k` (`v31.1` only) | -- (no cache, as `--cachedir`) |
| `--quiet`, `-q` | pytest's own `-q` |
| `--tmpdirprefix`, `-t` | pytest's own `--basetemp=<dir>` |
| `--failfast`, `-F` | pytest's own `-x` |
| `--filter` | pytest's own `-k` |
| `--resultsfile`, `-r` | pytest's own `--junitxml=<path>` |

`--nocleanup`: nothing in this tree's own fixtures ever removes a
node's datadir -- `NodeAdapter.stop` (`node.py`) only terminates the
process -- and pytest's own `tmp_path`/`tmp_path_factory` do not delete
a run's directories either when that run ends, only trimming older
numbered ones (`tmp_path_retention_count`, default 3) the *next* time a
run starts. `tests/integration/nocleanup_bitcoind_test.py` measures the
first half directly; naming `--basetemp=<dir>` is what makes the
directory a Core developer can find rather than one of the numbered
`pytest-of-<user>` ones.

`--tracerpc`: a `--tracerpc` flag on `tests/integration`'s own
collection wraps every adapter's RPC transport
(`bitcoin_core_rpc.BitcoinCoreRpcClient`'s own `transport=`) and prints
each request and reply as it is made, matching Core's own wording.

`--timeout-factor`: scales every wait this suite's own adapters and
`Peer` make by default -- `NodeAdapter.start`'s own startup wait and
`NodeAdapter.stop`'s own wait for the process to exit, `connect_nodes`,
`wait_until_disconnected`, `wait_until_tips_agree`,
`wait_until_mempools_agree` and `assert_debug_log` in `node.py` and
`debug_log.py` (`disconnect_nodes` and `sync_all` through the waits they
call), and `Peer`'s own
connection and per-call timeouts in `peer.py` -- through
`timeout_factor.py`'s own `scaled`, set once per process by
`tests/integration/conftest.py`'s own `pytest_configure`, the same
per-process scope `SkipCounts` already carries for the same `-n auto`
reason.

`--v2transport` and `--v1transport`: through the adapter rather than a
pytest option, since this suite has no central test-framework object
for a flag like Core's own to set a default on. `BitcoindAdapter`'s own
`extra_args=("-v2transport=1",)` or `("-v2transport=0",)` is Core's
own flag, node by node;
`tests/integration/v2transport_option_bitcoind_test.py` measures both
directions against `getpeerinfo`'s own `transport_protocol_type`.
`Capability.V2TRANSPORT` is declared by `BitcoindAdapter` alone: `Peer`
(`peer.py`) speaks only the plaintext v1 wire format, so the capability
covers node-to-node connections and not a `Peer`'s own, and
`BtclibNodeAdapter` never declares it -- its own `addnode` reads and
discards a `v2transport` parameter
(`btclib_node.rpc.callbacks.addnode`), with no BIP324 codec behind it.

`--valgrind`: no pytest option, since valgrind wraps a process rather
than a test; a `TF2_BITCOIND` naming a wrapper script that execs the
real binary under valgrind reaches the same effect through the adapter,
`NodeAdapter` never inspecting the executable path it is given beyond
passing it to `subprocess.Popen`.

### A version, and no release

Nothing here is released: `pyproject.toml`'s `version = "0"` is a
placeholder, no tag has ever agreed with it, and no command derives it.
Section 12's calendar versioning applies to what a release publishes,
from step 4 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220)
on. Until then this repository ships by being read.

### The editor

`.vscode/settings.json` and `.vscode/extensions.json` are tracked, and they
hold no preference: the recommended extensions are the tools
`.pre-commit-config.yaml` already runs, and the settings put the fixing ones
on save. Installing them is optional and changes nothing about what a local
run enforces.

Anything machine-local -- an interpreter path, a telemetry answer, a theme --
belongs in the editor's own user settings instead, those two files being
read by every checkout of this repository.

### Reproducing what CI runs

Each command below is the one a CI job runs. Keep this section true when a
workflow changes.

`test.yml`, the `coverage` job:

```shell
uv run --locked --no-default-groups --group test pytest
```

`lint.yml`, the `lint` job -- this file *is* the lint gate, so there is no
second list of tools anywhere:

```shell
uv run --locked --only-group lint \
    pre-commit run --all-files --show-diff-on-failure
```

`docs.yml`, the `docs` job -- the build, and then a read of the pages it
wrote. `reusable-docs.yml`'s own command carries no `--exact`, needing
none: a job's venv is fresh per run, which is what `--exact` reproduces
locally, added below for that reason and not present in the workflow
itself:

```shell
uv run --locked --exact --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
if grep -rn 'href="#\.\.\?/' docs/build/html --include='*.html'; then
    echo "::error::the links above resolve to no page (unresolved relative path)"
    exit 1
fi
```

What myst renders for a destination it cannot resolve is an anchor to an
id no page has. `-W` reports it because `docs/source/conf.py` resolves the
links the included root files carry and suppresses no myst warning; the
`grep` is what still finds one the day a suppression goes back in.

`vendored-vectors.yml`, the `vectors` job re-checks every pin of `TF2.md`
already at upstream's tip; the `census` job re-reads
`test/functional/test_framework/` recursively and compares it to the
ledger in both directions:

```shell
python .github/scripts/check_vendored_vectors.py \
    TF2.md "TF2.md pins behind upstream" --dry-run
python .github/scripts/tf2_ledger_census.py \
    TF2.md "test_framework has files TF2.md has no entry for" --dry-run
```

`codeql.yml` has no line here, and this repository does not carry it yet:
none of the workflows this step ships run a tool with no `uv run` of its
own.

`node-integration.yml`, the `bitcoind` job -- btclib-org/.github's
`reusable-integration-bitcoind.yml` is what runs it, so there is no
second command beyond the one above: `TF2_INTEGRATION=1 uv run pytest
tests/integration` against a bitcoind that job installs and verifies.
The `btclib-node` job needs the second interpreter the workflow's own
header explains, so reproducing it is that same command with
`TF2_BTCLIB_NODE_PYTHON` pointed at a 3.14 (or later, once `rocksdict`
ships one) interpreter `btclib-node` was installed into. `btclib-node-main`
is the same command again, `TF2_BTCLIB_NODE_PYTHON` pointed at an
interpreter carrying that project's own `main` rather than its last
release. `core-master` is `TF2_BITCOIND` pointed at a `bitcoind` built locally
from Bitcoin Core's own `master`, the job's own `Configure the build`
step naming the CMake options; its own verdict on a failure unique to
that build is `.github/scripts/tf2_master_verdict.py`, given the two
runs' own JUnit reports.

### What gates a merge, and what only reports

`lint.yml`, `test.yml`, `docs.yml` and `node-integration.yml`'s
`bitcoind` job produce the required checks, and `REPOSITORY.md` reads the
rule back from the endpoint rather than restating it. So a diff does not
reach a review without having passed them or passing them beside it on
the same sha, which is the reliance `REVIEWING.md` provides for.

`node-integration.yml`'s other jobs -- `btclib-node`, `core-master` and
`btclib-node-main` -- gate nothing anywhere: `continue-on-error: true` in
the workflow itself says so for each. `btclib-node`'s own disagreement
is ISS btclib-node#1072, filed on that repository's own tracker and not
a defect of this one's gates; `core-master` and `btclib-node-main` track
Core's own `master` and btclib-node's own `main` rather than the pinned
release under test, by [ISS 8](https://github.com/btclib-org/bitcoin-node-tests/issues/8)'s
decision of 2026-09-25.

| workflow | when | what it varies |
| --- | --- | --- |
| `test` | pull request, push | -- |
| `lint`, `docs` | pull request, push | -- |
| `node-integration` | pull request, push | -- |
| `claude-review` | pull request, and `@claude` in a comment | -- |
| `links` | weekly | -- |
| `vendored-vectors` | weekly | the pins in `TF2.md`, and the census |

Which day each of the rest runs is section 10 of
[the organization standard](https://github.com/btclib-org/.github), and
not this file's to restate.

The gates run one image on one interpreter: `ubuntu-latest`, and the
version `.python-version` names. `claude-review` gates nothing: a review
that gates a merge would make a model's judgement a branch rule.
