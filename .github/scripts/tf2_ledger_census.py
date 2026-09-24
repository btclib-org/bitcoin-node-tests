# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Read Core's `test/functional/test_framework/` and compare it to TF2.md.

`check_vendored_vectors.py` re-checks a pin already in the ledger and
cannot see a file Core *gains*: it walks the ledger's own entries and
asks upstream about each, so a new `test_framework/*.py` is invisible to
it (issue btclib-org/btclib#1751). This script asks the other question:
what does Core's directory hold today, and does every file in it have an
entry here -- in both directions, so a file Core has removed is reported
too, distinctly from one it has gained.

The listing is `git/trees?recursive=1`, checked for `.truncated` rather
than assumed complete, and never `contents`: that endpoint lists a
directory non-recursively, so it would answer without every file under
`crypto/` and report each of them as gone -- the failure mode that reads
as a real finding and is not one.

Reports under its own title, distinct from `check_vendored_vectors.py`'s
per-pin drift title, so a gained file and a stale pin are never the same
issue and one run's report never overwrites the other's.

    python .github/scripts/tf2_ledger_census.py \
        TF2.md "test_framework has files this ledger has no entry for"
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

_GH = shutil.which("gh") or "gh"

_UPSTREAM_DIR = "test/functional/test_framework"
_UPSTREAM_REPO = "bitcoin/bitcoin"

_HEADING = re.compile(rf"^### `{re.escape(_UPSTREAM_DIR)}/([^`]+)`$", re.MULTILINE)


def _default_branch_tip(repo: str) -> str:
    """Return the sha the repository's default branch points at.

    :param repo: the repository, `owner/name`.
    :returns: the commit sha.
    """
    result = subprocess.run(  # noqa: S603
        [_GH, "api", f"repos/{repo}/commits/HEAD", "--jq", ".sha"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def upstream_python_files(repo: str, directory: str, sha: str) -> list[str]:
    """List every `.py` path under a directory, at one commit, recursively.

    `git/trees?recursive=1` rather than `contents`, which lists one level
    at a time: a directory carrying a subdirectory would answer without
    what is under it, reporting every one of those paths as gone from
    upstream where they were never listed at all. `.truncated` is
    checked rather than assumed false -- GitHub's own warning that a
    tree over its own limit was cut, silently narrowing every comparison
    below to whatever fit.

    :param repo: the repository the tree belongs to, `owner/name`.
    :param directory: the directory to list, relative to the repository
        root, with no leading or trailing slash.
    :param sha: the commit to list the tree at.
    :returns: each `.py` path under `directory`, relative to it.
    :raises RuntimeError: where the API reports the listing truncated.
    """
    result = subprocess.run(  # noqa: S603
        [
            _GH,
            "api",
            "--method",
            "GET",
            f"repos/{repo}/git/trees/{sha}",
            "-f",
            "recursive=1",
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    tree = json.loads(result.stdout)
    if tree.get("truncated"):
        msg = (
            f"repos/{repo}/git/trees/{sha}?recursive=1 reports truncated: true --"
            " the listing below is a page of the tree, not the whole of it"
        )
        raise RuntimeError(msg)
    prefix = f"{directory}/"
    return sorted(
        entry["path"].removeprefix(prefix)
        for entry in tree["tree"]
        if entry["type"] == "blob"
        and entry["path"].startswith(prefix)
        and entry["path"].endswith(".py")
    )


def ledger_entries(ledger_text: str) -> set[str]:
    """Return the upstream-relative paths TF2.md carries an entry for.

    :param ledger_text: the ledger's own text.
    :returns: each entry's path, relative to `test/functional/test_framework/`.
    """
    return set(_HEADING.findall(ledger_text))


def _open_issue_number(title: str) -> str | None:
    result = subprocess.run(  # noqa: S603
        [
            _GH,
            "issue",
            "list",
            "--state",
            "open",
            "--search",
            f'"{title}" in:title',
            "--json",
            "number",
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
    )
    issues = json.loads(result.stdout)
    return str(issues[0]["number"]) if issues else None


def _issue_body(sha: str, gained: list[str], removed: list[str]) -> str:
    lines = [
        f"`test/functional/test_framework/` at `bitcoin/bitcoin@{sha[:12]}`",
        "disagrees with `TF2.md`'s own census. Deciding an entry for a",
        "gained file, or removing one for a file upstream no longer has,",
        "is not this report's to do.",
        "",
    ]
    if gained:
        lines.append("Gained upstream, no entry in TF2.md:")
        lines.extend(f"- `{path}`" for path in gained)
        lines.append("")
    if removed:
        lines.append("An entry in TF2.md, gone from upstream:")
        lines.extend(f"- `{path}`" for path in removed)
    return "\n".join(lines)


def report(title: str, sha: str, gained: list[str], removed: list[str]) -> None:
    """Open, update, or close the census's tracking issue.

    :param title: the issue title, distinct from the per-pin drift
        issue's own so that the two never share one.
    :param sha: the commit the census was read at.
    :param gained: paths upstream has that no entry names.
    :param removed: paths an entry names that upstream no longer has.
    """
    number = _open_issue_number(title)
    if not gained and not removed:
        if number is not None:
            subprocess.run(  # noqa: S603
                [
                    _GH,
                    "issue",
                    "close",
                    number,
                    "--comment",
                    f"Re-read at `{sha[:12]}`: TF2.md's census agrees with upstream.",
                ],
                check=True,
            )
        return
    body = _issue_body(sha, gained, removed)
    if number is None:
        subprocess.run(  # noqa: S603
            [_GH, "issue", "create", "--title", title, "--body", body],
            check=True,
        )
    else:
        subprocess.run(  # noqa: S603
            [_GH, "issue", "edit", number, "--body", body], check=True
        )


def main() -> int:
    """Compare the ledger to upstream, report drift, and say so on stdout.

    --dry-run skips opening, updating or closing the issue, the same
    switch `check_vendored_vectors.py` takes and for the same reason: a
    change to this script or to the ledger is exercised without editing
    whatever tracking issue happens to be open at the time.
    """
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = len(args) != len(sys.argv) - 1
    if len(args) != 2:
        print(
            f"usage: {Path(sys.argv[0]).name} <ledger path> <issue title> [--dry-run]",
            file=sys.stderr,
        )
        return 2
    ledger_path, title = Path(args[0]), args[1]

    sha = _default_branch_tip(_UPSTREAM_REPO)
    upstream = set(upstream_python_files(_UPSTREAM_REPO, _UPSTREAM_DIR, sha))
    entries = ledger_entries(ledger_path.read_text(encoding="utf-8"))

    gained = sorted(upstream - entries)
    removed = sorted(entries - upstream)

    for path in gained:
        print(f"GAINED: {path}")
    for path in removed:
        print(f"REMOVED: {path}")
    if not gained and not removed:
        print(f"TF2.md's census agrees with upstream at {sha[:12]}.")
    if not dry_run:
        report(title, sha, gained, removed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
