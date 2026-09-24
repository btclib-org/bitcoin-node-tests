# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""What `TF2.md` must say about Core's test framework, and must not.

The ledger is one entry per Python file of Core's
`test/functional/test_framework/`, and its whole value is that the
entries can be re-checked. Two things rot such a record and neither is
loud: an upstream file with no entry, and an entry whose covering module
has been renamed out from under it.

Core's set is transcribed rather than fetched, so the verdict does not
depend on somebody else's uptime, and the census is asserted in both
directions, so a file gained upstream and an entry that has outlived its
subject each land on a different assertion.
`test_both_sides_of_the_census_were_read` is the guard against the
failure that would otherwise make every comparison below pass for free
-- a regex reworded past the text it reads answers with an empty set,
and an empty set is a subset of everything.

What none of it can see is upstream gaining a file this transcription
does not carry: that is
`.github/scripts/tf2_ledger_census.py`'s question, run live and weekly,
never offline in this suite. The entry's own grammar is not
re-implemented here either. It is
`.github/scripts/check_vendored_vectors.py`'s, and that script is loaded
by path and asked to parse `TF2.md`: a heading whose fenced block that
parser skips is a heading the weekly re-check would silently never look
at, which is exactly the drift the ledger exists to prevent.

What is offline is that every upstream file this transcription carries
has an entry, that every entry is one the re-checker can put a question
to, and that no entry states a count.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

_ROOT = Path(__file__).parents[1]
_LEDGER = _ROOT / "TF2.md"
_CHECKER = _ROOT / ".github" / "scripts" / "check_vendored_vectors.py"

_UPSTREAM = "test/functional/test_framework"

# every Python file of that directory at the commit the entries pin,
# transcribed in the order `git/trees?recursive=1` lists them. A refresh
# of the ledger is a diff over this tuple.
_CORE_FILES = (
    "__init__.py",
    "address.py",
    "authproxy.py",
    "blockfilter.py",
    "blocktools.py",
    "compressor.py",
    "coverage.py",
    "crypto/bip324_cipher.py",
    "crypto/chacha20.py",
    "crypto/ellswift.py",
    "crypto/hkdf.py",
    "crypto/muhash.py",
    "crypto/poly1305.py",
    "crypto/ripemd160.py",
    "crypto/secp256k1.py",
    "crypto/siphash.py",
    "descriptors.py",
    "extendedkey.py",
    "ipc_util.py",
    "key.py",
    "mempool_util.py",
    "messages.py",
    "netutil.py",
    "p2p.py",
    "psbt.py",
    "script.py",
    "script_util.py",
    "segwit_addr.py",
    "signet.py",
    "socks5.py",
    "test_framework.py",
    "test_node.py",
    "test_shell.py",
    "util.py",
    "v2_p2p.py",
    "wallet.py",
    "wallet_util.py",
)

# the verdicts `TF2.md`'s own "The verdicts" section defines. A closed
# vocabulary rather than free text: a verdict spelled some other way is
# a row nobody can group with the rows it belongs with, and a verdict
# defined and never used is a definition that has outlived its subject
_VERDICTS = frozenset(
    {
        "covered",
        "covered in part",
        "vendored",
        "tf2's by decision",
        "tf2's (harness)",
        "empty upstream",
    }
)

# an entry's heading, which is the file's path in Core
_HEADING = re.compile(rf"^### `({_UPSTREAM}/[^`]+)`$", re.MULTILINE)

# the verdict opening the prose under a fenced block; what follows the
# closing asterisks is the entry's own argument and is not read here
_VERDICT = re.compile(r"^Verdict: \*\*([^*]+)\*\*", re.MULTILINE)

# a digit run, or a spelled-out cardinal as a whole word. "one" and
# "zero" are matched as digits only, never as words: in prose they are
# articles and pronouns far more often than counts
_NUMERAL = re.compile(
    r"(?i)\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
    r"nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
    r"hundred|thousand)\b"
)

# the numerals that name something rather than count it, subtracted
# before `_NUMERAL` runs: an ISO date, a specification as the bips
# repository spells one in a path, an RFC, an issue of either tracker in
# either form the prose uses -- including a qualified one,
# "btclib-org/btclib#2220" -- a rule or a step of ISS 2220's own
# numbering, and the variant number a hyphen introduces after a name, as
# in RIPEMD-160
_NOT_A_COUNT = re.compile(
    r"\b\d{4}-\d{2}(?:-\d{2})?\b"
    r"|(?i:\b(?:bip|slip)-\d+)"
    r"|\bRFC \d+"
    r"|(?i:\bissues?[ /]#?\d+)|\bISS \d+"
    r"|#\d+"
    r"|(?i:\b(?:rule|step)s?\s+\d+)"
    r"|(?<=[A-Za-z]-)\d+(?:-\d+)*"
    r"|(?<=[A-Za-z0-9]{12})[0-9a-f]{28}"  # the tail of a 40-hex commit sha
)

_TEXT = _LEDGER.read_text(encoding="utf-8")
_ENTRIES = tuple(_HEADING.findall(_TEXT))
_VERDICTS_READ = tuple(_VERDICT.findall(_TEXT))


def _prose_lines() -> list[str]:
    """Every line of the ledger outside a fenced block.

    A fence holds either the pin fields, whose `commit` and `behind` are
    facts of a pin that "Reading an entry" already defines, or a shell
    command, where a digit is an argument. Neither is prose stating a
    count, and scanning them would say so once per entry.
    """
    lines = []
    in_fence = False
    for line in _TEXT.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


@pytest.fixture
def checker(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Return the weekly re-checker, imported by path.

    Registered in `sys.modules` before it runs, its `Entry` and `Drift`
    dataclasses resolving their field types through the module name
    under `from __future__ import annotations`.
    """
    spec = importlib.util.spec_from_file_location("check_vendored_vectors", _CHECKER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "check_vendored_vectors", module)
    spec.loader.exec_module(module)
    return module


def test_both_sides_of_the_census_were_read() -> None:
    """A comparison over a side that came up empty is true of nothing.

    Every assertion below subtracts one set from another, and each of
    them passes for free where the set being subtracted from is empty.
    The ledger's side is read by a regex, which answers empty for a
    heading spelled some other way; Core's side is a literal tuple,
    which cannot be empty but can hold a path twice, in which case the
    two censuses disagree about a file neither reports.
    """
    assert _ENTRIES, "no entry heading was found in TF2.md at all"
    assert len(set(_ENTRIES)) == len(_ENTRIES), (
        f"a file has more than one entry: {sorted(_ENTRIES)}"
    )
    assert len(set(_CORE_FILES)) == len(_CORE_FILES), (
        f"a Core file is transcribed twice: {sorted(_CORE_FILES)}"
    )
    assert len(_VERDICTS_READ) == len(_ENTRIES), (
        f"{len(_ENTRIES)} entries carry {len(_VERDICTS_READ)} verdicts"
    )


def test_every_core_file_has_an_entry() -> None:
    """The census: a file of Core's directory is answered for."""
    entries = {path.removeprefix(f"{_UPSTREAM}/") for path in _ENTRIES}
    missing = sorted(set(_CORE_FILES) - entries)
    assert not missing, f"no entry in TF2.md for: {missing}"


def test_every_entry_names_a_core_file() -> None:
    """The other direction, which is where a deleted file lands.

    A file upstream renames or removes leaves an entry describing
    something that is not there, and the entry goes on reading as a
    statement about Core. The transcription above is what the entry is
    held to; refreshing one means refreshing both.
    """
    entries = {path.removeprefix(f"{_UPSTREAM}/") for path in _ENTRIES}
    unaccounted = sorted(entries - set(_CORE_FILES))
    assert not unaccounted, f"an entry names no transcribed Core file: {unaccounted}"


def test_every_verdict_is_one_of_the_defined_ones() -> None:
    """A verdict is from the closed vocabulary the ledger defines."""
    unknown = sorted({v for v in _VERDICTS_READ if v not in _VERDICTS})
    assert not unknown, f"a verdict TF2.md does not define: {unknown}"


def test_every_defined_verdict_is_used() -> None:
    """A definition nothing uses is a definition nothing holds to.

    The mirror of the assertion above, and the one that catches a
    verdict whose last entry was rewritten: the definition survives, is
    read as describing part of the ledger, and describes nothing.
    """
    unused = sorted(_VERDICTS - set(_VERDICTS_READ))
    assert not unused, f"TF2.md defines a verdict no entry carries: {unused}"


def test_no_entry_states_a_count() -> None:
    """Enforces CLAUDE.md's "Never state how many of anything a file holds".

    A count of the entries, of the covered files or of the uncovered ones
    is exactly the number that is exact today, wrong after the next
    upstream commit, and plausible throughout. Nothing in this ledger
    needs one, the entries being the fact such a number would summarize.
    """
    offenders = sorted(
        {
            line
            for line in _prose_lines()
            if _NUMERAL.search(_NOT_A_COUNT.sub(" ", line))
        }
    )
    assert not offenders, f"TF2.md states a numeral that is not exempt: {offenders}"


def test_the_numeral_pattern_still_matches() -> None:
    """The guard above passes for free if `_NUMERAL` matches nothing.

    The failure mode of every assertion written in the negative, and the
    one the file it reads cannot reveal. The strings below are the
    shapes a count of this ledger would take.
    """
    for text in (
        "The ledger has 36 entries.",
        "Thirty-six files, of which twelve are tf2's.",
        "- 7 files here",
        "Nine of them are the harness.",
    ):
        assert _NUMERAL.search(_NOT_A_COUNT.sub(" ", text)), text


def test_a_numeral_that_names_something_is_subtracted() -> None:
    """`_NOT_A_COUNT` fails in two directions and one of them is quiet.

    A shape that stops matching puts its line back in front of
    `_NUMERAL`, and the guard above says which line. A shape reaching
    past what it names swallows a count beside it and nothing says so,
    which is what the second group is for: each of those states a count
    *and* carries something the subtraction takes out.
    """
    for named in (
        "commit  0f206eed51e2d00aa78f709ecc427b484d04b4d5  2026-09-05",
        "[ISS 1120](https://github.com/btclib-org/btclib/issues/1120) is where",
        "hashlib offers no RIPEMD-160; its docstring carries",
        "secp256k1 alone, over BIP340's own vectors and MuHash3072",
    ):
        assert not _NUMERAL.search(_NOT_A_COUNT.sub(" ", named)), named
    for counted in (
        "Six entries were read at 2026-09-05.",
        "ISS 1120 left three of them out.",
    ):
        assert _NUMERAL.search(_NOT_A_COUNT.sub(" ", counted)), counted


def test_the_weekly_re_checker_reads_every_entry(checker: ModuleType) -> None:
    """Every entry is one the re-checker can ask upstream about.

    The grammar is that script's, so this is what says the ledger is in
    it: an entry whose fenced block lacks `repo`, `path` or `commit`, or
    whose `behind` does not read zero, is skipped by the script, and
    `.github/workflows/vendored-vectors.yml` runs that script over this
    file weekly -- so a skip is a pin nothing re-checks, silently.
    """
    entries, skipped = checker._entries_at_tip(_TEXT)
    assert not skipped, f"the re-checker would skip: {skipped}"
    assert [entry.heading for entry in entries] == [f"`{path}`" for path in _ENTRIES], (
        "the re-checker reads other headings than the ledger's own"
    )
    assert all(entry.repo == "bitcoin/bitcoin" for entry in entries)
    assert all(entry.path == entry.heading.strip("`") for entry in entries), (
        "an entry's `path` field and its heading name different files"
    )
    assert all(re.fullmatch(r"[0-9a-f]{40}", entry.commit) for entry in entries), (
        "a pin is not a full commit sha"
    )
