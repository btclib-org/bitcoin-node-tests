# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

How to work here is `CONTRIBUTING.md`, the same file in every repository
of the organization up to its last section; that section, *This
repository in particular*, is this tree's. `REPOSITORY.md` records the
settings that live outside the tree, and `REVIEWING.md` is what a pull
request is answered against.

## Architecture

Core's functional tests, rewritten on
[btclib](https://github.com/btclib-org/btclib), run against any node
that speaks bitcoin's RPC and p2p (issue
btclib-org/btclib#2220). `TF2.md` is the ledger of what Core's
`test/functional/test_framework/` needs and what covers it, one entry
per file: most of the directory is covered by `btclib` itself, and
`src/bitcoin_node_tests/` is the adapter and the test families built on
top of it -- `CONTRIBUTING.md`'s *The public surface* names the
adapter's own modules.

`TF2.md`'s citation rule governs every module under
`src/bitcoin_node_tests/`: a citation of a file under
`test/functional/test_framework/` names the file and the function, never a
line number, and leaves the revision to the ledger.

## The primary checkout is the maintainer's

Never work in it: no edit, no `git add`, no commit, no branch switch, no
rebase, no `git stash` — the hooks fix files in place. The one write
allowed there brings it forward, and only while it is on `main` and
`git status --porcelain` prints nothing; where it is not, stop:

```shell
checkout=<checkout>
```

```shell
git -C "${checkout:?}" pull --ff-only
```

Read it only after that, once `git -C <checkout> rev-parse HEAD
origin/main` prints one sha twice. A measurement that has to hold at a
named revision reads `git -C <checkout> show <sha>:<path>` instead.

Every session works in a worktree of its own, from its first edit, named
`wt-<tracker>-<issue>-<repo>-<role>` — `wt-github-255-btclib-writer` for
issue 255 of `btclib-org/.github`'s tracker, worked in `btclib` by a
writer. The environment is created there, with the command `CONTRIBUTING.md`
names under *The environment and the gates*. Every path is written out in
full:

```shell
git worktree add \
  <scratchpad>/wt-<tracker>-<issue>-<repo>-<role> origin/main -b <branch>
```

Removing it is part of finishing:

```shell
git worktree remove --force <scratchpad>/wt-<tracker>-<issue>-<repo>-<role>
```

`refs/stash` and the local `main` are shared by every worktree: never
`git stash`, and move `main` only by the fast-forward above.

## Model

Default model: Sonnet; Opus for design decisions with conflicting
constraints. Do not use Fable unless instructed.

## Non-obvious facts that will otherwise waste a session

- **The version is a placeholder.** `pyproject.toml`'s `version = "0"`
  is `CONTRIBUTING.md`'s *A version, and no release*: nothing has been
  published, and no command derives the number.
- **The `contents` API endpoint is refused for a directory listing, on
  purpose.** It lists one level at a time, so a directory carrying a
  subdirectory -- `test/functional/test_framework/crypto/` -- answers
  without what is under it, and every file down there reads as gone from
  upstream. `.github/scripts/tf2_ledger_census.py` uses
  `git/trees?recursive=1` instead, checking `.truncated` rather than
  assuming the listing complete.
- **`entry_path`, never `path`, for a shell variable holding a file
  path.** `TF2.md`'s own *Re-checking a pin* section states the reason:
  in `zsh`, the shell this is read in, `path` is tied to `PATH` as an
  array, so assigning a file path to it replaces the reader's `PATH`
  with that one entry.
- **`check_vendored_vectors.py` re-checks a pin already in the ledger and
  cannot see a file Core gains.** That is `tf2_ledger_census.py`'s
  question, run separately and weekly, under a title distinct from the
  per-pin drift issue's own -- the two must never share one issue.
- **A rebase over a `main` that gained its own `CHANGELOG.md` entry eats
  the blank line above the branch's entry.** `.gitattributes` says why,
  and what names it. Prove the repair by rebuilding the file as the new
  base's `CHANGELOG.md`, a blank line and the branch's entry as written,
  then `cmp` it with the committed file; a copy with one byte changed
  must differ. An expected file built from the rebased diff lacks the
  blank line too, so it matches the broken file.

## Conventions to match

- **Workflows**: section 10 of the organization standard is what every
  workflow does. `actionlint` and `zizmor` are hooks, and both must
  report zero findings.
- **The prose style -- tone, comments, docstrings, no history -- is
  section 9 of the organization standard**, which `CONTRIBUTING.md`'s
  *Documentation and comments* is the pointer to.
- **CHANGELOG.md gets an entry for anything a reader would notice.** No
  `RELEASE_NOTES.md`: section 2 of the organization standard gives
  that file to a tier-1 tree, and this one publishes nothing.
- **Never state how many of anything a file holds**: `tests/tf2_ledger_test.py`
  fails on a stated count in `TF2.md`.

## Verifying

Run the command as documented before claiming it works, and read its
exit code rather than its filtered output. `REVIEWING.md`'s *The gates
are the evidence* is where that rule is written for a reader who is not
this one.

Prefer measuring to asserting: every claim in this file was checked
against the tree, and the tree changes.
