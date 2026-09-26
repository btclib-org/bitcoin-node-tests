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


# `--timeout-factor` and `--tracerpc` are `pytest_addoption`'s own, imported
# here rather than restated: a nested session that never spawns a real node
# still exercises the option's registration and, for `--timeout-factor`,
# that `pytest_configure` actually sets `timeout_factor`'s own multiplier
# -- issue bitcoin-node-tests#36
_OPTION_CONFTEST = """
    from tests.integration.conftest import pytest_addoption, pytest_configure
"""

_TIMEOUT_FACTOR_TEST = """
    from bitcoin_node_tests.timeout_factor import scaled

    def test_the_factor_option_reaches_the_module():
        assert scaled(2.0) == 5.0
"""


def test_timeout_factor_option_sets_the_module_s_own_factor(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--timeout-factor 2.5` is what `timeout_factor.scaled` then applies."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile(_TIMEOUT_FACTOR_TEST)
    result = pytester.runpytest_subprocess("--timeout-factor", "2.5")
    result.assert_outcomes(passed=1)


def test_timeout_factor_option_defaults_to_1x(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No `--timeout-factor` given: `1.0`, matching Core's own default."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile("""
        from bitcoin_node_tests.timeout_factor import scaled

        def test_the_factor_is_unscaled():
            assert scaled(2.0) == 2.0
    """)
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)


# what pytest-timeout enforces is what is asserted, not `--timeout` alone:
# it reads its setting once, in its own `pytest_configure`, so a scaled
# option written after that read would change nothing. The header is the
# controller's reading; `_env_timeout`, pytest-timeout's private attribute
# holding that reading, is checked inside the test, so under `-n 2` it is
# a worker's own
_PER_TEST_TIMEOUT_INI = """
    [pytest]
    timeout = 40
"""

_PER_TEST_TIMEOUT_TEST = """
    def test_the_bound(request):
        assert request.config._env_timeout == {expected!r}
"""


@pytest.mark.parametrize(
    "args, expected",
    [
        ((), 40.0),
        (("--timeout-factor", "2.5"), 100.0),
        (("--timeout-factor", "2.5", "-p", "xdist", "-n", "2"), 100.0),
        (("--timeout-factor", "2.5", "--timeout", "7"), 7.0),
    ],
)
def test_timeout_factor_option_scales_the_ini_timeout(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
    expected: float,
) -> None:
    """The ini's own `timeout` grows with the waits; a given `--timeout` not."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    monkeypatch.delenv("PYTEST_TIMEOUT", raising=False)
    pytester.makeini(_PER_TEST_TIMEOUT_INI)
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile(_PER_TEST_TIMEOUT_TEST.format(expected=expected))
    result = pytester.runpytest_subprocess(*args)
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([f"timeout: {expected}s"])


def test_timeout_factor_option_leaves_pytest_timeout_env_as_given(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`PYTEST_TIMEOUT` is the caller's own bound, and is not scaled."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    monkeypatch.setenv("PYTEST_TIMEOUT", "9")
    pytester.makeini(_PER_TEST_TIMEOUT_INI)
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile("""
        def test_the_bound(request):
            assert request.config.getoption("timeout") is None
    """)
    result = pytester.runpytest_subprocess("--timeout-factor", "2.5")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["timeout: 9.0s"])


def test_tracerpc_option_defaults_to_false(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unset, `--tracerpc` reads `False` -- Core's own `--tracerpc` default."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile("""
        def test_tracerpc_defaults_to_false(request):
            assert request.config.getoption("--tracerpc") is False
    """)
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)


def test_tracerpc_option_is_recognized_when_given(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--tracerpc` is a real option, not an "unrecognized arguments" error."""
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(_OPTION_CONFTEST)
    pytester.makepyfile("""
        def test_tracerpc_is_true(request):
            assert request.config.getoption("--tracerpc") is True
    """)
    result = pytester.runpytest_subprocess("--tracerpc")
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("args, expected", [((), False), (("--tracerpc",), True)])
def test_make_adapter_builds_with_the_tracerpc_option(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
    expected: bool,
) -> None:
    """`make_adapter` hands `--tracerpc`, given or not, to what it builds.

    The class it is handed only records its own `trace_rpc`: no node
    starts, so the nested session needs neither `TF2_INTEGRATION` nor a
    binary.
    """
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    pytester.makeconftest(
        _OPTION_CONFTEST + "    from tests.integration.conftest import make_adapter\n"
    )
    pytester.makepyfile(f"""
        class Recorder:
            def __init__(self, *args, trace_rpc):
                self.trace_rpc = trace_rpc

        def test_make_adapter(make_adapter):
            built = make_adapter(Recorder, "node", "datadir", 1, 2)
            assert built.trace_rpc is {expected}
    """)
    result = pytester.runpytest_subprocess(*args)
    result.assert_outcomes(passed=1)
