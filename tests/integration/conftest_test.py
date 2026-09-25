# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The printed skip tally is the sum over the whole run, xdist or not.

Issue btclib-org/bitcoin-node-tests#16: `SkipCounts` is one instance per
process, and `-n auto` starts several -- a controller that runs no test
of its own (`xdist.dsession.DSession.pytest_collection` refuses
collection there) and one worker per `-n` slot, each with its own empty
tally at start-up. A test built on calling `pytest_sessionfinish` by hand
proves nothing about this: the hazard is in how pytest and xdist drive
that hook across several real processes, which is exactly what a hand
call skips over. `pytester.runpytest_subprocess` is what actually starts
that many processes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

# the project root, so the nested session below -- which starts in its
# own temporary directory, well outside this tree -- can still import
# `tests.integration.conftest`: that package is not installed, unlike
# `bitcoin_node_tests` itself, so it needs its own directory on
# `PYTHONPATH` rather than relying on site-packages
_ROOT = Path(__file__).resolve().parents[2]

# the nested session's own conftest: `pytest_sessionfinish`,
# `pytest_testnodedown` and `skip_counts` are imported from the real
# `tests/integration/conftest.py`, so this exercises that module's own
# code rather than a copy of it. The skip translation is the three lines
# `tests/conftest.py` carries for the same purpose, restated rather than
# imported -- matching `tests/capability_test.py`'s own end-to-end test,
# which restates it for the same reason: driving the real thing through
# an actual nested session, the point of either test, does not need it
# imported too
_CONFTEST = """
    import pytest
    from bitcoin_node_tests.capability import MissingCapabilityError
    from tests.integration.conftest import (
        pytest_sessionfinish,
        pytest_testnodedown,
        skip_counts,
    )

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(item):
        del item
        try:
            return (yield)
        except MissingCapabilityError as exc:
            pytest.skip(str(exc))
"""

# three skips of `mine`, one of `raw_message`, and one declared capability
# that passes rather than skipping -- so the run's own outcome count and
# the printed tally are two different assertions, neither standing in for
# the other
_TESTS = """
    from bitcoin_node_tests.capability import Capability, require

    def test_mine_1(skip_counts):
        require(Capability.MINE, frozenset(), skip_counts)

    def test_mine_2(skip_counts):
        require(Capability.MINE, frozenset(), skip_counts)

    def test_mine_3(skip_counts):
        require(Capability.MINE, frozenset(), skip_counts)

    def test_raw_message(skip_counts):
        require(Capability.RAW_MESSAGE, frozenset(), skip_counts)

    def test_connect_is_declared(skip_counts):
        require(Capability.CONNECT, frozenset({Capability.CONNECT}), skip_counts)
"""


def _run(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, *args: str
) -> pytest.RunResult:
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(_CONFTEST)
    pytester.makepyfile(_TESTS)
    return pytester.runpytest_subprocess(*args)


def test_the_tally_sums_every_xdist_worker_s_own_skips(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under a real multi-worker split, the printed total still counts four.

    `-n 2` rather than the tree's own `-n auto`: `auto` picks a worker
    count from the machine running the suite, which a real multi-process
    split does not need to be reproducible -- any `-n` above zero puts a
    controller that runs nothing in front of workers that split the five
    tests between them, which is the one property this test is about.
    """
    result = _run(pytester, monkeypatch, "-p", "xdist", "-n", "2")
    result.assert_outcomes(passed=1, skipped=4)
    result.stdout.fnmatch_lines(["*skips per capability:", "mine: 3", "raw_message: 1"])


def test_the_tally_is_unchanged_with_no_worker_split(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`-n 0`: one process runs every test, and its own tally is the total."""
    result = _run(pytester, monkeypatch, "-p", "xdist", "-n", "0")
    result.assert_outcomes(passed=1, skipped=4)
    result.stdout.fnmatch_lines(["*skips per capability:", "mine: 3", "raw_message: 1"])
