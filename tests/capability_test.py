# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`Capability.require` skips exactly on a missing capability, and counts it."""

from __future__ import annotations

import pytest

from bitcoin_node_tests.capability import (
    Capability,
    MissingCapabilityError,
    SkipCounts,
    require,
)
from tests.conftest import _translate_missing_capability


def test_require_passes_through_a_declared_capability() -> None:
    """A capability the node declares is answered by returning, not skipping."""
    counts = SkipCounts()
    require(Capability.MINE, frozenset({Capability.MINE}), counts)
    assert list(counts) == []


def test_require_skips_a_missing_capability() -> None:
    """A capability the node does not declare is a `MissingCapabilityError`."""
    counts = SkipCounts()
    with pytest.raises(MissingCapabilityError, match="connect"):
        require(Capability.CONNECT, frozenset(), counts)
    assert list(counts) == [(Capability.CONNECT, 1)]


def test_require_counts_every_skip_against_its_own_capability() -> None:
    """Two skips of the same capability are one count of two, not two rows."""
    counts = SkipCounts()
    for _ in range(2):
        with pytest.raises(MissingCapabilityError):
            require(Capability.MINE, frozenset(), counts)
    with pytest.raises(MissingCapabilityError):
        require(Capability.CONNECT, frozenset(), counts)
    assert list(counts) == [(Capability.CONNECT, 1), (Capability.MINE, 2)]


def test_report_names_no_test_where_nothing_was_recorded() -> None:
    """An empty session's own report says so instead of printing nothing."""
    assert (
        SkipCounts().report() == "skips per capability: no test asked for one this run"
    )


def test_report_names_every_recorded_capability() -> None:
    """The report holds one line per capability, sorted by its own value."""
    counts = SkipCounts()
    with pytest.raises(MissingCapabilityError):
        require(Capability.MINE, frozenset(), counts)
    with pytest.raises(MissingCapabilityError):
        require(Capability.CONNECT, frozenset(), counts)
    report = counts.report()
    assert report == "skips per capability:\nconnect: 1\nmine: 1"


def test_the_autouse_fixture_turns_the_exception_into_a_skip() -> None:
    """`tests/conftest.py`'s own translation, driven directly as a generator.

    A test that lets `MissingCapabilityError` escape uncaught -- rather than
    catching it itself, as every test above does -- is what would
    exercise this through an ordinary pytest run; driving the fixture's
    own generator function is the same exception meeting the same
    `except` clause, without a nested pytest session to read the
    outcome of.
    """
    # pytest's own stubs type a fixture as `FixtureFunctionDefinition` and
    # do not declare `__wrapped__`, though pytest always sets it to the
    # undecorated generator function -- the same attribute
    # `inspect.unwrap` and `functools.wraps` both rely on elsewhere.
    fixture = _translate_missing_capability.__wrapped__()  # type: ignore[attr-defined]
    next(fixture)
    with pytest.raises(pytest.skip.Exception, match="mine"):
        fixture.throw(MissingCapabilityError("node does not declare mine"))
