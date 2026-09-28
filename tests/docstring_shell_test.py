# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""A docstring's shell command continues its line with one backslash.

A command a docstring gives -- `uv run pytest \` above the module it
runs -- is copied into a shell, which continues a line only where it
ends in an odd run of backslashes: an even run is escaped backslashes,
and the next line runs as a command of its own. In a raw docstring `\\`
is two characters, so what is checked is the docstring's value, the
text a reader copies, rather than its source.
"""

import ast
from pathlib import Path

import pytest

_ROOT = Path(__file__).parents[1]
# the trees whose Python files carry docstrings; `[tool.uv.build-backend]`
# leaves `.github` out of the sdist, the suite runs from one, and `rglob`
# under a missing directory yields nothing
_SOURCES = ("src", "tests", "docs", ".github")


def _docstrings() -> list[tuple[str, str]]:
    """Return each docstring of the tree, beside the file holding it."""
    found = []
    for source in _SOURCES:
        for path in sorted((_ROOT / source).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
                ):
                    docstring = ast.get_docstring(node, clean=False)
                    if docstring:
                        found.append((str(path.relative_to(_ROOT)), docstring))
    return found


def _broken_continuations(docstring: str) -> list[str]:
    """Return every line a shell would not continue onto the next."""
    broken = []
    for line in docstring.splitlines():
        stripped = line.rstrip()
        run = len(stripped) - len(stripped.rstrip("\\"))
        if run and run % 2 == 0:
            broken.append(stripped)
    return broken


def test_every_continuation_is_one_backslash() -> None:
    """No docstring line ends in an even run of backslashes."""
    broken = [
        f"{path}: {line}"
        for path, docstring in _docstrings()
        for line in _broken_continuations(docstring)
    ]
    assert not broken, "\n".join(broken)


def test_a_continuation_was_found_at_all() -> None:
    """The test above does not pass because the walk read nothing.

    The run commands of `tests/integration/` continue a line, so a walk
    that reaches them finds a line ending in a backslash.
    """
    assert any(
        line.rstrip().endswith("\\")
        for path, docstring in _docstrings()
        if path.startswith("tests/integration/")
        for line in docstring.splitlines()
    )


@pytest.mark.parametrize(
    "docstring, broken",
    [
        ("uv run pytest \\\n    tests/integration", []),
        ("uv run pytest \\\\\n    tests/integration", ["uv run pytest \\\\"]),
        ("uv run pytest \\\\\\\n    tests/integration", []),
        ("uv run pytest tests/integration", []),
    ],
)
def test_broken_continuations(docstring: str, broken: list[str]) -> None:
    """One backslash continues, two do not, three do again."""
    assert _broken_continuations(docstring) == broken
