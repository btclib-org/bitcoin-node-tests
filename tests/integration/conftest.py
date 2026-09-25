# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""What the integration tests need, and what makes them skip.

Two switches per node, and `TF2_INTEGRATION` gates both: these tests
start a real process, open a real socket and write to disk, none of
which an ordinary `uv run pytest` should do to somebody who asked for
the unit suite. The second switch is the node itself -- found on `PATH`
or named for bitcoind, importable by the named interpreter for
btclib-node -- because an opt-in that fails for a missing program would
report a defect that is not one.

Read from btclib's own `tests/integration/conftest.py` for shape, not
shared with it: this repository's own `NodeAdapter` subclasses are what
start and stop a node here (rule 5 of issue btclib-org/btclib#2220 --
tf2 writes its own adapter), where btclib's fixture spawns `bitcoind` by
hand, having no adapter of its own to reach for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import SkipCounts
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# one tally per process, shared by every fixture and test below:
# `pytest_sessionfinish` reports it once, rather than once per node this
# session happened to drive. Under `-n auto` this module loads once per
# xdist worker and once in the controller, so this is one tally *per
# process* rather than one for the run -- `pytest_sessionfinish` and
# `pytest_testnodedown` below are what turn that into the single total
# rule 4 asks for.
_skip_counts = SkipCounts()


@pytest.fixture(scope="session")
def skip_counts() -> SkipCounts:
    """Return this session's own tally, shared by every test that skips."""
    return _skip_counts


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Hand a worker's own tally to the controller, or report the total.

    Every one of the processes `-n auto` starts runs this hook, and
    `session.config.workeroutput` is what tells them apart: it exists
    only inside an xdist worker (`xdist.remote` sets it at worker
    start-up), never in the controller and never in a plain `-n 0` run.
    A worker's own tally counts only the tests *it* ran, so a worker
    stashes it there instead of reporting it -- the controller reads it
    back through `node.workeroutput` in `pytest_testnodedown` below, and
    folds it in before this same hook runs on the controller itself. A
    plain run started with `-n 0` is not a worker either, and needs no
    folding: it is the one process that ran every test, so the tally
    below is already the whole run's.

    A fixture's own teardown print is captured with everything else a
    test writes and shown only where that test failed; this hook runs
    once its own process's session is over and is not subject to that
    capture -- rule 4's "the run prints a skip count" needs that, a
    green run that skipped every `Capability.MINE` case otherwise
    printing nothing at all.

    :param session: whose `.config` says whether this process is an
        xdist worker.
    :param exitstatus: unused; the hook's own signature names it.
    """
    del exitstatus
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        workeroutput["skip_counts"] = _skip_counts.as_mapping()
        return
    print(_skip_counts.report())  # noqa: T201


def pytest_testnodedown(node: object, error: object | None) -> None:
    """Fold one xdist worker's own tally into the controller's, as it exits.

    xdist calls this hook only in the controller process, once per
    worker as it goes down (finishes or crashes) -- and, for every
    worker, before the controller reaches its own `pytest_sessionfinish`
    above, which is what reports the sum. Absent under `-n 0`, there
    being no worker to go down.

    :param node: the worker that just finished; `node.workeroutput` is
        what `pytest_sessionfinish` above stashed in its own process,
        crossed over by xdist as plain data. Typed as `object` because
        `xdist.workermanage.WorkerController` ships no `py.typed`
        marker for this file's `strict = true` to check against.
    :param error: unused; the hook's own signature names it.
    """
    del error
    workeroutput = getattr(node, "workeroutput", None)
    if workeroutput is not None:
        _skip_counts.add_mapping(workeroutput.get("skip_counts", {}))


def _require_integration() -> None:
    if not os.environ.get("TF2_INTEGRATION"):
        pytest.skip("set TF2_INTEGRATION=1 to run the integration tests")


@pytest.fixture(scope="session")
def bitcoind_path() -> str:
    """Return the bitcoind to run, skipping the whole module without one."""
    _require_integration()
    path = os.environ.get("TF2_BITCOIND") or shutil.which("bitcoind")
    if path is None:
        pytest.skip("no bitcoind: name one in TF2_BITCOIND or put it on PATH")
    return path


@pytest.fixture(scope="session")
def bitcoind_adapter(
    bitcoind_path: str, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[BitcoindAdapter]:
    """Yield a `BitcoindAdapter` over a regtest node started this session."""
    adapter = BitcoindAdapter(
        bitcoind_path, tmp_path_factory.mktemp("bitcoind"), free_port(), free_port()
    )
    adapter.start()
    try:
        yield adapter
    finally:
        adapter.stop()


@pytest.fixture
def bitcoind_cluster(
    bitcoind_path: str, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[Callable[[int], list[BitcoindAdapter]]]:
    """Yield a factory for `count` fresh `BitcoindAdapter`s, stopped after.

    Function-scoped, unlike `bitcoind_adapter` above: the first family's
    multi-node tests (`p2p_block_sync`, `p2p_compactblocks_hb`) each want
    their own clean-chain topology rather than one node shared across the
    whole session, and each call of the factory this yields starts one
    more node over a fresh data directory and a fresh pair of ports.
    """
    started: list[BitcoindAdapter] = []

    def _start(count: int) -> list[BitcoindAdapter]:
        for _ in range(count):
            adapter = BitcoindAdapter(
                bitcoind_path,
                tmp_path_factory.mktemp("bitcoind"),
                free_port(),
                free_port(),
            )
            adapter.start()
            started.append(adapter)
        return started

    try:
        yield _start
    finally:
        for adapter in reversed(started):
            adapter.stop()


@pytest.fixture(scope="session")
def btclib_node_python() -> str:
    """Return the interpreter to run btclib-node with, skipping without one.

    `TF2_BTCLIB_NODE_PYTHON` names it; `sys.executable` where unset. This
    project carries no dependency group installing `btclib-node`:
    measured live, `uv sync` resolving it against this project's own
    `requires-python = ">=3.15"` fails outright on its own dependency
    `rocksdict`, which ships no `cp315` wheel yet -- `pyproject.toml`'s
    own comment on `[dependency-groups]` says so. So `btclib-node` needs
    an interpreter of its own, installed into some other environment by
    hand, and named here rather than assumed. Probed by actually
    importing the package under that interpreter rather than by
    `shutil.which`: there is no console script this adapter runs
    (`btclib_node.py`'s own docstring is why), so nothing on `PATH`
    would ever answer for it.
    """
    _require_integration()
    python = os.environ.get("TF2_BTCLIB_NODE_PYTHON") or sys.executable
    probe = subprocess.run(  # noqa: S603
        [python, "-c", "import btclib_node"], check=False, capture_output=True
    )
    if probe.returncode != 0:
        pytest.skip(
            f"no btclib_node importable by {python}: install it there, or name"
            " another interpreter in TF2_BTCLIB_NODE_PYTHON"
        )
    return python


@pytest.fixture(scope="session")
def btclib_node_adapter(
    btclib_node_python: str, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[BtclibNodeAdapter]:
    """Yield a `BtclibNodeAdapter`, a regtest node started this session."""
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        tmp_path_factory.mktemp("btclib-node"),
        free_port(),
        free_port(),
    )
    adapter.start()
    try:
        yield adapter
    finally:
        adapter.stop()
