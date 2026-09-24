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
btclib-org/btclib#2220). This step carries the organization's apparatus
and `TF2.md`, the ledger of what Core's
`test/functional/test_framework/` needs and what covers it, one entry
per file: what covers most of the directory today is `btclib` itself,
this repository's own adapter and test families being later steps of
the same issue.

`TF2.md`'s citation rule governs every module this repository will
publish: a citation of a file under `test/functional/test_framework/`
names the file and the function, never a line number, and leaves the
revision to the ledger.

## The primary checkout is the maintainer's

**Never work in it.** No edit, no `git add`, no commit, no branch
switch, no rebase, no `git stash` — the hooks fix files in place. It is a
local reference only, and it stays on `main`.

Reading it is fine, but `git fetch` moves `refs/remotes/origin/main` and
leaves the work tree where it was, so a `grep` or a `Read` against the
checkout answers for whenever it was last brought forward, not for now.
The read that cannot go stale is `git show origin/main:<path>`: it
answers from the ref `git fetch` just moved, never from the tree.

Where the checkout has to be current rather than merely readable, a
fast-forward of a clean `main` brings it up:

```shell
git fetch origin && git merge --ff-only origin/main
```

That writes no commit, switches no branch and runs no hook, so it is on
the permitted side of *never work in it*, not an exception to it. Stop
if the checkout is not on `main` or is not clean: that is no longer
bringing it forward.

**Every session works in a worktree**, its own, from the first edit, named
`wt-<tracker>-<issue>-<repo>-<role>` rather than after the issue alone, most
general part first: an issue filed in `btclib-org/.github`'s tracker is the key
and the repository is a detail of it — `btclib-org/.github#255` is one issue
owed by seven repositories, `btclib-org/.github#177` by two — so the repository
is what varies underneath an issue rather than the other way round, which is why
`repo` comes after `issue`. Naming it that way also sorts every worktree of one
issue together, which is what a port leaves behind.

Each of the four parts earns its place against a different collision,
and none of them is the same collision. `tracker` is the repository
whose issue tracker holds the issue: an issue number is unique only
within one tracker, so `btclib-org/.github#45` and
`btclib-org/btclib#45` are different issues that would otherwise name
the same worktree. `issue` is what prevents the collision that has
actually happened — two worktrees of different work sharing a generic
basename in one repository's own `.git`, keyed on its path's basename.
`repo` prevents a different collision, a *path* one rather than a `.git`
one: two repositories each keep their own `.git/worktrees/<basename>`
and cannot collide there, but the workers of one session share one
scratchpad directory, so a session carrying one issue into several
repositories computes the same target path for each of them, and `git
worktree add` refuses a directory that already exists — or worse, a
second worker reads the first one's tree. `role` covers the narrower
case of a coder and its reviewer holding a worktree at once, which the
ordinary sequence avoids by each removing its own.

An issue of `btclib-org/.github`'s tracker, worked in `btclib` by a coder, names
its worktree `wt-github-255-btclib-coder`. The environment is created in the
worktree, not the checkout, by whatever that tree's own `CONTRIBUTING.md` names
under *The environment and the gates*, and a session reads that section, not
this one, for the command. The editing, the gates and the commits all happen in
the worktree before the push.

```shell
WT=<scratchpad>/wt-<tracker>-<issue>-<repo>-<role>
git worktree add "$WT" origin/main -b <branch>
git -C "$WT" push origin HEAD:refs/heads/<branch>
```

`-b <branch>` sits after the path and the commit-ish so that the placeholder
ends the command, which is section 9 of `btclib-org/.github`'s rule. With the
placeholder ahead of `"$WT"`, its `<` and its `>` are redirections performed
left to right, so the `>` is reached only where the reader's own directory
already holds the name `branch`: there the `<` succeeds, the line runs, and the
`>` takes `"$WT"` as its target — a path with no directory at it is the file it
creates. Ordinarily nothing holds that name, so the `<` fails first (`no such
file or directory: branch`) and the line ends before the `>` opens anything.

The push names the worktree with `git -C "$WT"` because a `cd` binds the
shell that runs it: a session that runs each line as its own command
starts the next one in the directory it began in, the primary checkout,
so a push after a `cd` offers that checkout's `HEAD` instead of the
worktree's. `env -C <dir>` is the same binding for a command that takes
no `-C` of its own. Neither binding rescues the assignment above it: a
session that loses the `cd` loses `WT` with it, and `git -C ""` is
documented to leave the working directory unchanged, so that push lands
the same way, exit 0 and no diagnostic. That silence is `git`'s rather
than the binding's: the BSD `env` macOS ships documents no case for an
empty `-C` and refuses one — `cannot change directory to ''`, exit 125 —
so a line bound with `env -C` stops there instead of running against the
wrong tree. What the `-C` buys is a path that can be written out in
full; write it out.

Removing the worktree is part of finishing, and it stands in a block of
its own: the block above ends in a placeholder, and a shell that
discards that line as a parse error reads the next as a fresh command —
which, in one block, is this line against whatever `$WT` already held.
Standing alone it is a second fence, so `${WT:?}` is what it writes:
with `$WT` unset or empty the expansion fails and the removal does not
run. Those are the only cases it catches — a `$WT` an earlier session or
command left holding a path expands, and the removal runs against
whatever worktree that path names.

```shell
git worktree remove --force "${WT:?}"
```

**Never `git stash` in a worktree either: `refs/stash` is shared.** A
worktree isolates files, not refs, so `git stash push` pushes onto the
same stack every other session pops from. Commit to your own branch
instead.

**Do not rewrite `refs/heads/main`, and move it only onto
`origin/main`.** That name is the local branch's, and no ruleset reaches
it: a ruleset binds the forge's copy. The fast-forward above moves it
onto `origin/main` and is inside that, where a merge, a commit on `main`
or an `update-ref` to a branch tip leaves the ref somewhere
`origin/main` is not. Your own branch is what you push, and the pull
request is what moves `origin/main`.

## Model

The default model for this repository is Sonnet. Switch to Opus only
for architectural decisions with conflicting constraints -- design
choices with non-obvious trade-offs, the shape of the adapter later
steps build, diagnosis where the symptom does not point to the cause.
Use `/model opus` for the session, then switch back to Sonnet.

Do not use Fable unless explicitly instructed.

## Non-obvious facts that will otherwise waste a session

- **The version is a placeholder.** `pyproject.toml`'s `version = "0"`
  is what `CONTRIBUTING.md`'s *A version, and no release* is for: this
  tree publishes nothing before step 4 of
  [ISS 2220](https://github.com/btclib-org/btclib/issues/2220), and no
  command derives the number.
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
- **This tree's own minute in section 10's calendar is `44`.** Chosen as
  the next multiple of four past `btclib-wallet`'s `40`, the newest row
  at the time this repository was created; `btclib-org/.github`'s own
  `README.md` is the record once its own pull request lands one, this
  tree's `REPOSITORY.md` in the meantime.

## Conventions to match

- **Workflows**: every action pinned to a commit SHA with the tag in a
  trailing comment; every workflow declares `permissions: contents:
  read` and `timeout-minutes`; concurrency groups are named literally,
  never through `github.workflow`; `checkout` passes
  `persist-credentials: false`; uv commands pass `--locked`, never
  `--frozen`. `actionlint` and `zizmor` are hooks, and both must stay at
  zero findings.
- **The prose style -- tone, comments, docstrings, no history -- is
  section 9 of the organization standard**, which `CONTRIBUTING.md`'s
  *Documentation and comments* is the pointer to.
- **CHANGELOG.md gets an entry for anything a user would notice.** No
  `RELEASE_NOTES.md` yet: section 2 of the organization standard gives
  that file to a tier-1 tree, and this one publishes nothing.
- **Never state how many of anything a file holds** -- `TF2.md`'s own
  `tests/tf2_ledger_test.py` fails on a stated count, with no
  allowlist beside it.

## Verifying

Run the command as documented before claiming it works, and read its
exit code rather than its filtered output. `REVIEWING.md`'s *The gates
are the evidence* is where that rule is written for a reader who is not
this one.

Prefer measuring to asserting: every claim in this file was checked
against the tree, and the tree changes.
