# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the weekly pin re-check of `.github/scripts`.

Its external dependency is `gh`. Every test here replaces
`subprocess.run` with `FakeGh`, which answers the way a real
`gh api repos/<repo>/commits` would rather than reaching GitHub: with
the commit that last touched a path, the one that deleted or renamed
it included, and with an empty list for a path the branch walked never
held.

The script is loaded by path, `.github/scripts` being no package, the
same idiom `tf2_ledger_test.py` uses for it.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).parents[1] / ".github" / "scripts" / "check_vendored_vectors.py"
)

_PATH = "test/functional/test_framework/bignum.py"

_PIN = "0d1301b47a35"

# the API's own full sha for the commit that deleted the pinned file
_REMOVING_SHA = "3ed772d221" + "0" * 30

_LEDGER = f"""\
### `bignum.py`

```text
repo    bitcoin/bitcoin
path    {_PATH}
commit  {_PIN}
behind  0
```
"""


@pytest.fixture
def checker(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Return the script, imported by path, registered before it runs."""
    spec = importlib.util.spec_from_file_location("check_vendored_vectors", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_vendored_vectors", module)
    spec.loader.exec_module(module)
    return module


class FakeGh:
    """A `subprocess.run` stand-in, answering `gh api .../commits` alone.

    `commits` maps a path to the (sha, date) the listing names first; a
    path absent from it answers with an empty list. Every call is
    recorded in `calls`.
    """

    def __init__(self) -> None:
        self.commits: dict[str, tuple[str, str]] = {}
        self.calls: list[list[str]] = []

    def __call__(
        self, argv: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        """Record the call, and answer the path it asked about."""
        self.calls.append(list(argv))
        path = next(a.removeprefix("path=") for a in argv if a.startswith("path="))
        found = self.commits.get(path)
        commits = (
            [
                {
                    "sha": found[0],
                    "commit": {"committer": {"date": f"{found[1]}T00:00:00Z"}},
                }
            ]
            if found
            else []
        )
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(commits))


@pytest.fixture
def fake_gh(checker: ModuleType, monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    """Install a `FakeGh` in place of the script's `subprocess.run`."""
    fake = FakeGh()
    monkeypatch.setattr(checker.subprocess, "run", fake)
    return fake


def test_latest_commit_answers_none_for_a_path_never_held(
    checker: ModuleType, fake_gh: FakeGh
) -> None:
    """An empty listing is a path the branch walked never held."""
    assert checker._latest_commit("bitcoin/bitcoin", _PATH) is None


def test_latest_commit_passes_a_ref_as_the_sha_parameter(
    checker: ModuleType, fake_gh: FakeGh
) -> None:
    """A `ref` is the branch the listing walks."""
    checker._latest_commit("bitcoin/bitcoin", _PATH, "some-branch")
    assert "sha=some-branch" in fake_gh.calls[0]


def test_a_removing_commit_is_drift_that_may_be_a_removal(
    checker: ModuleType, fake_gh: FakeGh, tmp_path: Path
) -> None:
    """A deleted pin's tip is the deleting commit, named as possibly that.

    [ISS 150](https://github.com/btclib-org/bitcoin-node-tests/issues/150).
    """
    ledger = tmp_path / "TF2.md"
    ledger.write_text(_LEDGER, encoding="utf-8")
    fake_gh.commits[_PATH] = (_REMOVING_SHA, "2019-10-30")
    drifted, skipped = checker.find_drift(ledger)
    assert skipped == []
    assert [d.latest_commit for d in drifted] == [_REMOVING_SHA]
    assert not drifted[0].has_no_tip
    body = checker._issue_body(ledger, drifted, skipped)
    assert (
        f"the latest commit touching `{_PATH}` is now `{_REMOVING_SHA}`"
        " (2019-10-30), `bitcoin/bitcoin` -- which may have deleted or renamed"
        " the file rather than changed it"
    ) in body


def test_an_empty_listing_names_the_branch_walked(
    checker: ModuleType, fake_gh: FakeGh, tmp_path: Path
) -> None:
    """No commit at all is named as a path that branch never held."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(
        _LEDGER.replace("behind", "ref     pr-branch\nbehind"), encoding="utf-8"
    )
    drifted, skipped = checker.find_drift(ledger)
    assert [d.has_no_tip for d in drifted] == [True]
    body = checker._issue_body(ledger, drifted, skipped)
    assert (
        "no commit on `pr-branch` of `bitcoin/bitcoin` touches"
        f" `{_PATH}` -- a path that branch never held"
    ) in body
    unnamed = checker.Drift(checker.Entry("h", "bitcoin/bitcoin", _PATH, _PIN), "", "")
    assert "no commit on the default branch of" in checker._issue_body(
        ledger, [unnamed], []
    )
