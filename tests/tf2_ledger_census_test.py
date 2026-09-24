# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the recursive Core-directory census of `.github/scripts`.

Its only external dependency is `gh`, called for the default branch tip,
for the recursive tree listing, and for the tracking issue. Every test
here replaces `subprocess.run` with `FakeGh`, which answers each call the
way a real `gh api`/`gh issue` would rather than reaching GitHub.

The script is loaded by path, `.github/scripts` being no package, the
same idiom `tf2_ledger_test.py` uses for `check_vendored_vectors.py`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).parents[1] / ".github" / "scripts" / "tf2_ledger_census.py"


@pytest.fixture
def census(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Return the script, imported by path, registered before it runs."""
    spec = importlib.util.spec_from_file_location("tf2_ledger_census", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "tf2_ledger_census", module)
    spec.loader.exec_module(module)
    return module


class FakeGh:
    """A `subprocess.run` stand-in, answering by which `gh` call this is.

    `tip` is the sha `_default_branch_tip` should read back. `files` is
    the tree entries the recursive listing answers with, as (path, type)
    pairs; `truncated` toggles the flag the listing carries. `open_issue`
    is the number `_open_issue_number` should report open, or None for no
    issue open. Every call is recorded in `calls`.
    """

    def __init__(self) -> None:
        self.tip = "0" * 40
        self.files: list[tuple[str, str]] = []
        self.truncated = False
        self.open_issue: int | None = None
        self.calls: list[list[str]] = []

    def __call__(
        self, argv: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        """Record the call, and answer as the `gh` sub-command it names."""
        self.calls.append(list(argv))
        if argv[1] == "api" and any(a.endswith("/commits/HEAD") for a in argv):
            return subprocess.CompletedProcess(argv, 0, stdout=self.tip)
        if argv[1] == "api" and any("/git/trees/" in a for a in argv):
            tree = {
                "truncated": self.truncated,
                "tree": [{"path": path, "type": kind} for path, kind in self.files],
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(tree))
        if argv[1] == "issue" and argv[2] == "list":
            issues = (
                [{"number": self.open_issue}] if self.open_issue is not None else []
            )
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(issues))
        return subprocess.CompletedProcess(argv, 0, stdout="")


@pytest.fixture
def fake_gh(census: ModuleType, monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    """Install a `FakeGh` in place of the script's own `subprocess.run`."""
    fake = FakeGh()
    monkeypatch.setattr(census.subprocess, "run", fake)
    return fake


_DIR = "test/functional/test_framework"


def test_upstream_python_files_lists_recursively(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """Every `.py` blob under the directory, at any depth, and nothing else."""
    fake_gh.files = [
        (f"{_DIR}", "tree"),
        (f"{_DIR}/address.py", "blob"),
        (f"{_DIR}/crypto", "tree"),
        (f"{_DIR}/crypto/hkdf.py", "blob"),
        (f"{_DIR}/bip340_test_vectors.csv", "blob"),
        ("test/functional/other_dir/x.py", "blob"),
    ]
    found = census.upstream_python_files("bitcoin/bitcoin", _DIR, "abc")
    assert found == ["address.py", "crypto/hkdf.py"]


def test_upstream_python_files_refuses_a_truncated_listing(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """`.truncated: true` is checked rather than assumed false."""
    fake_gh.truncated = True
    with pytest.raises(RuntimeError, match="truncated"):
        census.upstream_python_files("bitcoin/bitcoin", _DIR, "abc")


def test_upstream_python_files_forces_a_get(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """`-f recursive=1` alone makes `gh api` default to POST, which 404s.

    Measured against the real endpoint: `gh api
    repos/<owner>/<repo>/git/trees/<sha> -f recursive=1` answers "Not
    Found" because `-f` switches `gh api`'s own default method to POST,
    and this endpoint takes none; `--method GET` ahead of it is what
    keeps the call a read. `FakeGh` answers either way, so nothing but
    this assertion on the recorded call would have caught it -- it is
    what a real dispatch of `vendored-vectors.yml` did catch, `FakeGh`
    answering the wrong method just as readily as the right one.
    """
    census.upstream_python_files("bitcoin/bitcoin", _DIR, "abc")
    [call] = [c for c in fake_gh.calls if any("/git/trees/" in a for a in c)]
    assert "--method" in call
    assert call[call.index("--method") + 1] == "GET"


def test_ledger_entries_reads_the_headings(census: ModuleType) -> None:
    r"""The upstream-relative path of every `### \`...\`` heading."""
    text = f"### `{_DIR}/address.py`\n\ntext\n\n### `{_DIR}/crypto/hkdf.py`\n\ntext\n"
    assert census.ledger_entries(text) == {"address.py", "crypto/hkdf.py"}


def test_report_opens_an_issue_on_a_disagreement(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """A gained or a removed path opens an issue naming it."""
    census.report("title", "a" * 40, ["signet.py"], ["gone.py"])
    create = next(call for call in fake_gh.calls if call[1:3] == ["issue", "create"])
    body = create[create.index("--body") + 1]
    assert "signet.py" in body
    assert "gone.py" in body


def test_report_edits_an_open_issue_instead_of_creating_a_second(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """A second disagreement updates the issue the first one opened."""
    fake_gh.open_issue = 42
    census.report("title", "a" * 40, ["signet.py"], [])
    edit = next(call for call in fake_gh.calls if call[1:3] == ["issue", "edit"])
    assert edit[3] == "42"


def test_report_closes_an_open_issue_once_the_census_agrees(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """No disagreement closes whatever issue was tracking one."""
    fake_gh.open_issue = 42
    census.report("title", "a" * 40, [], [])
    close = next(call for call in fake_gh.calls if call[1:3] == ["issue", "close"])
    assert close[3] == "42"


def test_report_does_nothing_where_nothing_was_open(
    census: ModuleType, fake_gh: FakeGh
) -> None:
    """No disagreement and no open issue: nothing to close either."""
    census.report("title", "a" * 40, [], [])
    assert not any(call[1:3] == ["issue", "close"] for call in fake_gh.calls)


def test_main_end_to_end(
    census: ModuleType,
    fake_gh: FakeGh,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`main` reads argv, compares, prints, and reports unless `--dry-run`."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(f"### `{_DIR}/address.py`\n\ntext\n", encoding="utf-8")
    fake_gh.files = [
        (f"{_DIR}/address.py", "blob"),
        (f"{_DIR}/signet.py", "blob"),
    ]

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), "a title", "--dry-run"])
    assert census.main() == 0
    out = capsys.readouterr().out
    assert "GAINED: signet.py" in out
    assert not any(call[1] == "issue" for call in fake_gh.calls)

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), "a title"])
    assert census.main() == 0
    assert any(call[1] == "issue" for call in fake_gh.calls)


def test_main_reports_a_removed_path(
    census: ModuleType,
    fake_gh: FakeGh,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry upstream no longer has prints REMOVED, not GAINED."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(
        f"### `{_DIR}/address.py`\n\ntext\n\n### `{_DIR}/gone.py`\n\ntext\n",
        encoding="utf-8",
    )
    fake_gh.files = [(f"{_DIR}/address.py", "blob")]

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), "a title", "--dry-run"])
    assert census.main() == 0
    out = capsys.readouterr().out
    assert "REMOVED: gone.py" in out
    assert "GAINED" not in out


def test_main_reports_no_disagreement(
    census: ModuleType,
    fake_gh: FakeGh,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ledger that matches upstream prints agreement and nothing else."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(f"### `{_DIR}/address.py`\n\ntext\n", encoding="utf-8")
    fake_gh.files = [(f"{_DIR}/address.py", "blob")]

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), "a title", "--dry-run"])
    assert census.main() == 0
    out = capsys.readouterr().out
    assert "agrees with upstream" in out
    assert "GAINED" not in out
    assert "REMOVED" not in out


def test_main_usage_error(census: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Too few or too many arguments is a usage error, exit 2."""
    monkeypatch.setattr(sys, "argv", ["prog", "one-arg"])
    assert census.main() == 2
