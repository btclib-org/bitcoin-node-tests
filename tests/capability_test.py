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
from tests.conftest import pytest_runtest_call


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


def test_the_hookwrapper_generator_converts_a_thrown_exception() -> None:
    """`pytest_runtest_call`'s own generator, driven the way pluggy drives it.

    A `wrapper=True` hookimpl's generator is exactly what pluggy's own
    `_multicall` sends a result into or throws an exception into at its
    `yield` -- unlike a plain autouse fixture's teardown, which only ever
    calls `next` regardless of the wrapped test's own outcome (the shape
    this hook replaced, and the reason a manual `throw` on that one
    would have proven nothing about a real pytest run).
    """
    call = pytest_runtest_call(item=None)  # type: ignore[arg-type]
    next(call)
    with pytest.raises(pytest.skip.Exception, match="mine"):
        call.throw(MissingCapabilityError("node does not declare mine"))


def test_the_hookwrapper_turns_the_exception_into_a_skip(
    pytester: pytest.Pytester,
) -> None:
    """`tests/conftest.py`'s own translation, driven through a real session.

    The unit test above drives the generator directly, matching pluggy's
    own protocol; this one confirms the same thing end to end, through
    an actual nested pytest session.
    """
    pytester.makeconftest(
        """
        import pytest
        from bitcoin_node_tests.capability import MissingCapabilityError

        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_call(item):
            del item
            try:
                return (yield)
            except MissingCapabilityError as exc:
                pytest.skip(str(exc))
        """
    )
    pytester.makepyfile(
        """
        from bitcoin_node_tests.capability import MissingCapabilityError

        def test_it():
            raise MissingCapabilityError("node does not declare mine")
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(skipped=1)
