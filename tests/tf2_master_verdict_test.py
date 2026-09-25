# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the master-only failure classifier of `.github/scripts`.

Its only external dependency is `gh`, called once per master-only
failure for the Core file's last commit on `master`. Every test here
replaces `subprocess.run` with `FakeGh`, which answers the way a real
`gh api repos/bitcoin/bitcoin/commits` would rather than reaching
GitHub.

The script is loaded by path, `.github/scripts` being no package, the
same idiom `tf2_ledger_census_test.py` and `tf2_ledger_test.py` use for
their own scripts.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).parents[1] / ".github" / "scripts" / "tf2_master_verdict.py"

_DIR = "test/functional"


@pytest.fixture
def verdict(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Return the script, imported by path, registered before it runs."""
    spec = importlib.util.spec_from_file_location("tf2_master_verdict", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "tf2_master_verdict", module)
    spec.loader.exec_module(module)
    return module


class FakeGh:
    """A `subprocess.run` stand-in, answering `gh api .../commits` alone.

    `commits` maps a path to the (sha, date) `_latest_commit` should
    report for it; a path absent from it answers with no commit at all,
    matching upstream having nothing to say about a renamed or deleted
    file. Every call is recorded in `calls`.
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
            if found is not None
            else []
        )
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(commits))


@pytest.fixture
def fake_gh(verdict: ModuleType, monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    """Install a `FakeGh` in place of the script's own `subprocess.run`."""
    fake = FakeGh()
    monkeypatch.setattr(verdict.subprocess, "run", fake)
    return fake


def _junit(cases: list[tuple[str, str, str]]) -> str:
    """Build a minimal JUnit XML report.

    :param cases: one `(classname, name, outcome)` triple per testcase,
        `outcome` one of `"pass"`, `"fail"` or `"skip"`.
    :returns: the report's own text.
    """
    bodies = []
    for classname, name, outcome in cases:
        inner = {
            "pass": "",
            "fail": '<failure message="boom">traceback</failure>',
            "skip": '<skipped message="no node"/>',
        }[outcome]
        bodies.append(
            f'<testcase classname="{classname}" name="{name}" time="0.01">'
            f"{inner}</testcase>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<testsuites><testsuite name="pytest">{"".join(bodies)}'
        "</testsuite></testsuites>"
    )


def _module(text: str) -> str:
    """Return module text opening with the docstring a test module carries."""
    return f'# Copyright (c) The btclib developers\n"""{text}"""\n'


_LEDGER = """\
## The per-test ledger

| Core test | pin | read at | bitcoind | btclib-node |
| --- | --- | --- | --- | --- |
| `feature_blocksdir.py` | `0d1301b47a35` | 2026-03-24 | pass | skip (blk) |
| `p2p_invalid_messages.py` (wire) | `3fd68a95e68b` | 2026-04-07 | pass | pass |
| `p2p_invalid_messages.py` (inv, wire) | same | same | pass | fail |
| `feature_framework_miniwallet.py` \
| [`fa5f29774872`](https://github.com/bitcoin/bitcoin/commit/fa5f29774872) \
| 2025-12-16 | pass | skip |
"""


def test_ledger_pins_reads_the_first_row_and_resolves_same(
    verdict: ModuleType,
) -> None:
    """A `same` cell repeats the nearest explicit row above it."""
    pins = verdict.ledger_pins(_LEDGER)
    assert pins["feature_blocksdir.py"] == "0d1301b47a35"
    assert pins["p2p_invalid_messages.py"] == "3fd68a95e68b"


def test_ledger_pins_reads_a_markdown_link_cell(verdict: ModuleType) -> None:
    """A pin cell can carry a link around the backticked sha, not just one."""
    pins = verdict.ledger_pins(_LEDGER)
    assert pins["feature_framework_miniwallet.py"] == "fa5f29774872"


def test_ledger_pins_ignores_the_header_and_separator_rows(
    verdict: ModuleType,
) -> None:
    """`Core test` and `---` are not files, and name no pin."""
    pins = verdict.ledger_pins(_LEDGER)
    assert "Core test" not in pins
    assert "---" not in pins


def test_parse_junit_classifies_fail_skip_and_pass(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """A failure or an error is fail, a skip is skip, else pass."""
    report = tmp_path / "report.xml"
    report.write_text(
        _junit(
            [
                ("m", "test_a", "pass"),
                ("m", "test_b", "fail"),
                ("m", "test_c", "skip"),
            ]
        ),
        encoding="utf-8",
    )
    results = verdict.parse_junit(report)
    assert results == {"m::test_a": "pass", "m::test_b": "fail", "m::test_c": "skip"}


def test_parse_junit_reads_an_error_as_a_failure(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """An `<error>` element is a failure too, not a status of its own."""
    report = tmp_path / "report.xml"
    report.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites><testsuite name="pytest">'
        '<testcase classname="m" name="test_a" time="0.0">'
        '<error message="boom">traceback</error></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    assert verdict.parse_junit(report) == {"m::test_a": "fail"}


def test_master_only_failures_excludes_a_failure_shared_with_the_pin(
    verdict: ModuleType,
) -> None:
    """A test failing on both runs is not master-only."""
    master = {"m::a": "fail", "m::b": "fail", "m::c": "pass"}
    pinned = {"m::a": "fail", "m::b": "pass"}
    assert verdict.master_only_failures(master, pinned) == ["m::b"]


def test_master_only_failures_is_empty_where_nothing_disagrees(
    verdict: ModuleType,
) -> None:
    """No failure at all against master reports no master-only failure."""
    assert verdict.master_only_failures({"m::a": "pass"}, {"m::a": "pass"}) == []


def test_core_file_for_test_reads_the_module_own_citation(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """The Core file a test module names in its own first paragraph."""
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "feature_blocksdir_bitcoind_test.py").write_text(
        _module(
            "Core's `feature_blocksdir`, rewritten on tf2's own harness.\n\n"
            "Read from Core's `test/functional/feature_blocksdir.py`"
            " (`0d1301b47a35`, 2026-03-24) rather than ported whole."
        ),
        encoding="utf-8",
    )
    core_file = verdict.core_file_for_test(
        "tests.integration.feature_blocksdir_bitcoind_test", tmp_path
    )
    assert core_file == "feature_blocksdir.py"


def test_core_file_for_test_tells_two_modules_of_one_file_apart(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """`p2p_invalid_messages` and its own `_misbehaving` module name one file.

    A module-name transform would have to special-case this pairing; this
    reads the citation each module states instead, which needs none.
    """
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "p2p_invalid_messages_bitcoind_test.py").write_text(
        _module("Read from Core's `test/functional/p2p_invalid_messages.py`"),
        encoding="utf-8",
    )
    (module / "p2p_invalid_messages_misbehaving_bitcoind_test.py").write_text(
        _module(
            "Four more of its own checks.\n\n"
            "Read from Core's `test/functional/p2p_invalid_messages.py`"
        ),
        encoding="utf-8",
    )
    first = verdict.core_file_for_test(
        "tests.integration.p2p_invalid_messages_bitcoind_test", tmp_path
    )
    second = verdict.core_file_for_test(
        "tests.integration.p2p_invalid_messages_misbehaving_bitcoind_test", tmp_path
    )
    assert first == second == "p2p_invalid_messages.py"


def test_core_file_for_test_answers_none_for_a_missing_module(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """A module this repository has since removed names no Core file."""
    assert (
        verdict.core_file_for_test("tests.integration.gone_bitcoind_test", tmp_path)
        is None
    )


def test_core_file_for_test_answers_none_with_no_citation(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """A module carrying no citation sentence names no Core file either."""
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "odd_bitcoind_test.py").write_text(
        _module("Nothing here mentions Core's own path at all."), encoding="utf-8"
    )
    assert (
        verdict.core_file_for_test("tests.integration.odd_bitcoind_test", tmp_path)
        is None
    )


def test_latest_commit_reads_the_sha_and_the_date(
    verdict: ModuleType, fake_gh: FakeGh
) -> None:
    """The commit `gh api` answers for the path, sha and date both."""
    fake_gh.commits[f"{_DIR}/feature_blocksdir.py"] = ("abc123", "2026-05-01")
    assert verdict._latest_commit(f"{_DIR}/feature_blocksdir.py") == (
        "abc123",
        "2026-05-01",
    )


def test_latest_commit_answers_none_for_a_path_gone_upstream(
    verdict: ModuleType, fake_gh: FakeGh
) -> None:
    """No commit touching the path at all is a path upstream no longer has."""
    assert verdict._latest_commit(f"{_DIR}/gone.py") is None


def test_classify_stale_port(verdict: ModuleType) -> None:
    """The file has moved since the pin: this repository's own defect."""
    assert verdict.classify("0d1301b47a35", "fedcba987654") == "stale port"


def test_classify_candidate_regression(verdict: ModuleType) -> None:
    """The file has not moved: a finding for Core, once checked by hand."""
    assert verdict.classify("0d1301b47a35", "0d1301b47a35") == "candidate regression"


def test_verdicts_classifies_a_master_only_failure(
    verdict: ModuleType, fake_gh: FakeGh, tmp_path: Path
) -> None:
    """A failing test maps to its Core file, its pin, and a verdict."""
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "feature_blocksdir_bitcoind_test.py").write_text(
        _module(
            "Read from Core's `test/functional/feature_blocksdir.py`"
            " (`0d1301b47a35`, 2026-03-24)."
        ),
        encoding="utf-8",
    )
    fake_gh.commits[f"{_DIR}/feature_blocksdir.py"] = ("fedcba987654", "2026-06-01")
    master = {"tests.integration.feature_blocksdir_bitcoind_test::test_a": "fail"}
    pinned = {"tests.integration.feature_blocksdir_bitcoind_test::test_a": "pass"}
    lines = verdict.verdicts(_LEDGER, master, pinned, tmp_path)
    assert len(lines) == 1
    assert "stale port" in lines[0]
    assert "feature_blocksdir.py" in lines[0]


def test_verdicts_names_a_test_with_no_core_citation(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """No module on disk for the failing classname: named, not raised."""
    master = {"tests.integration.gone_bitcoind_test::test_a": "fail"}
    lines = verdict.verdicts(_LEDGER, master, {}, tmp_path)
    assert len(lines) == 1
    assert "no Core file citation" in lines[0]


def test_verdicts_names_a_file_the_ledger_has_no_row_for(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """A Core file this ledger fixture never pinned is named, not guessed at."""
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "rpc_uptime_bitcoind_test.py").write_text(
        _module("Read from Core's `test/functional/rpc_uptime.py` (`x`, 2026-06-13)."),
        encoding="utf-8",
    )
    master = {"tests.integration.rpc_uptime_bitcoind_test::test_a": "fail"}
    lines = verdict.verdicts(_LEDGER, master, {}, tmp_path)
    assert len(lines) == 1
    assert "names no row" in lines[0]


def test_verdicts_names_a_path_gone_upstream(
    verdict: ModuleType, fake_gh: FakeGh, tmp_path: Path
) -> None:
    """A ledger pin whose path upstream no longer has is named as such."""
    module = tmp_path / "tests" / "integration"
    module.mkdir(parents=True)
    (module / "feature_blocksdir_bitcoind_test.py").write_text(
        _module(
            "Read from Core's `test/functional/feature_blocksdir.py`"
            " (`0d1301b47a35`, 2026-03-24)."
        ),
        encoding="utf-8",
    )
    master = {"tests.integration.feature_blocksdir_bitcoind_test::test_a": "fail"}
    lines = verdict.verdicts(_LEDGER, master, {}, tmp_path)
    assert len(lines) == 1
    assert "no commit touching this path" in lines[0]


def test_verdicts_is_empty_with_no_master_only_failure(
    verdict: ModuleType, tmp_path: Path
) -> None:
    """Nothing failing only against master reports nothing at all."""
    assert verdict.verdicts(_LEDGER, {"m::a": "pass"}, {"m::a": "pass"}, tmp_path) == []


def test_main_usage_error(verdict: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fewer or more than three arguments is a usage error, exit 2."""
    monkeypatch.setattr(sys, "argv", ["prog", "one", "two"])
    assert verdict.main() == 2


def test_main_prints_agreement_with_no_master_only_failure(
    verdict: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No disagreement prints agreement and nothing else."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(_LEDGER, encoding="utf-8")
    master = tmp_path / "master.xml"
    master.write_text(_junit([("m", "test_a", "pass")]), encoding="utf-8")
    pinned = tmp_path / "pinned.xml"
    pinned.write_text(_junit([("m", "test_a", "pass")]), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), str(master), str(pinned)])
    monkeypatch.chdir(tmp_path)
    assert verdict.main() == 0
    out = capsys.readouterr().out
    assert "No test fails" in out


def test_main_prints_a_master_only_verdict(
    verdict: ModuleType,
    fake_gh: FakeGh,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A master-only failure prints its own report line."""
    ledger = tmp_path / "TF2.md"
    ledger.write_text(_LEDGER, encoding="utf-8")
    classname = "tests.integration.feature_blocksdir_bitcoind_test"
    module_dir = tmp_path / "tests" / "integration"
    module_dir.mkdir(parents=True)
    (module_dir / "feature_blocksdir_bitcoind_test.py").write_text(
        _module(
            "Read from Core's `test/functional/feature_blocksdir.py`"
            " (`0d1301b47a35`, 2026-03-24)."
        ),
        encoding="utf-8",
    )
    fake_gh.commits[f"{_DIR}/feature_blocksdir.py"] = ("0d1301b47a35", "2026-03-24")
    master = tmp_path / "master.xml"
    master.write_text(_junit([(classname, "test_a", "fail")]), encoding="utf-8")
    pinned = tmp_path / "pinned.xml"
    pinned.write_text(_junit([(classname, "test_a", "pass")]), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["prog", str(ledger), str(master), str(pinned)])
    monkeypatch.chdir(tmp_path)
    assert verdict.main() == 0
    out = capsys.readouterr().out
    assert "candidate regression" in out
    assert "feature_blocksdir.py" in out
