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

`--tracerpc` and `--timeout-factor` are Core's own `test_framework.py`
options, restated as pytest ones -- CONTRIBUTING.md's own *Running
against a Core developer's own build* has the full mapping, and
`--nocleanup`, `--v2transport` and `--v1transport` are named there too,
neither needing a flag of its own here.
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
from bitcoin_node_tests.node import free_ports
from bitcoin_node_tests.timeout_factor import set_factor
from tests.conftest import fold_worker_tally, stash_or_report, stop_all

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

    Every one of the processes `-n auto` starts runs this hook; the body
    is `tests/conftest.py`'s own `stash_or_report`, which
    `[tool.coverage.run]`'s own `omit` cannot reach there, this module
    being under the omitted `tests/integration/*`.

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
    stash_or_report(_skip_counts, getattr(session.config, "workeroutput", None))


def pytest_testnodedown(node: object, error: object | None) -> None:
    """Fold one xdist worker's own tally into the controller's, as it exits.

    xdist calls this hook only in the controller process, once per
    worker as it goes down (finishes or crashes) -- and, for every
    worker, before the controller reaches its own `pytest_sessionfinish`
    above, which is what reports the sum. Absent under `-n 0`, there
    being no worker to go down. The body is `tests/conftest.py`'s own
    `fold_worker_tally`.

    :param node: the worker that just finished; `node.workeroutput` is
        what `pytest_sessionfinish` above stashed in its own process,
        crossed over by xdist as plain data. Typed as `object` because
        `xdist.workermanage.WorkerController` ships no `py.typed`
        marker for this file's `strict = true` to check against.
    :param error: unused; the hook's own signature names it.
    """
    del error
    fold_worker_tally(_skip_counts, getattr(node, "workeroutput", None))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add Core's own `--tracerpc` and `--timeout-factor`, spelled Core's way.

    Only reached on an invocation naming `tests/integration` on the
    command line, pytest's initial-conftest collection running ahead of
    argument parsing over the paths given rather than over `testpaths`:
    measured live, a bare `uv run pytest --tracerpc` from the repository
    root answers "unrecognized arguments", where
    `uv run pytest tests/integration --tracerpc` does not. That matches
    every documented invocation of this module, which always names the
    path.
    """
    parser.addoption(
        "--tracerpc",
        action="store_true",
        default=False,
        help="print every RPC call this suite's adapters make, and its reply",
    )
    parser.addoption(
        "--timeout-factor",
        type=float,
        default=1.0,
        help="scale every wait this suite's adapters and Peer make by this factor",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Set this process's own `--timeout-factor`, before any node starts.

    One call per process, matching `_skip_counts`'s own scope above: an
    xdist worker runs its own `pytest_configure`, and every worker is
    handed the same command line, so every process scales the same way.

    :param config: the pytest session configuration.
    """
    set_factor(config.getoption("--timeout-factor"))


@pytest.fixture(scope="session")
def trace_rpc(request: pytest.FixtureRequest) -> bool:
    """Return whether `--tracerpc` was given, for a fixture to pass on."""
    return bool(request.config.getoption("--tracerpc"))


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
    bitcoind_path: str, tmp_path_factory: pytest.TempPathFactory, trace_rpc: bool
) -> Iterator[BitcoindAdapter]:
    """Yield a `BitcoindAdapter` over a regtest node started this session."""
    rpc_port, p2p_port = free_ports(2)
    adapter = BitcoindAdapter(
        bitcoind_path,
        tmp_path_factory.mktemp("bitcoind"),
        rpc_port,
        p2p_port,
        trace_rpc=trace_rpc,
    )
    adapter.start()
    try:
        yield adapter
    finally:
        adapter.stop()


@pytest.fixture
def bitcoind_cluster(
    bitcoind_path: str, tmp_path_factory: pytest.TempPathFactory, trace_rpc: bool
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
            rpc_port, p2p_port = free_ports(2)
            adapter = BitcoindAdapter(
                bitcoind_path,
                tmp_path_factory.mktemp("bitcoind"),
                rpc_port,
                p2p_port,
                trace_rpc=trace_rpc,
            )
            adapter.start()
            started.append(adapter)
        return started

    try:
        yield _start
    finally:
        stop_all(started)


@pytest.fixture(scope="session")
def btclib_node_python() -> str:
    """Return the interpreter to run btclib-node with, skipping without one.

    `TF2_BTCLIB_NODE_PYTHON` names it; `sys.executable` where unset. This
    project carries no dependency group installing `btclib-node`,
    kept separate from this environment regardless of version (issue
    bitcoin-node-tests#42) -- `pyproject.toml`'s own comment on
    `[dependency-groups]` has the reason. So `btclib-node` needs an
    interpreter of its own, installed into some other environment by
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
    btclib_node_python: str, tmp_path_factory: pytest.TempPathFactory, trace_rpc: bool
) -> Iterator[BtclibNodeAdapter]:
    """Yield a `BtclibNodeAdapter`, a regtest node started this session."""
    rpc_port, p2p_port = free_ports(2)
    adapter = BtclibNodeAdapter(
        btclib_node_python,
        tmp_path_factory.mktemp("btclib-node"),
        rpc_port,
        p2p_port,
        trace_rpc=trace_rpc,
    )
    adapter.start()
    try:
        yield adapter
    finally:
        adapter.stop()


@pytest.fixture
def mixed_cluster(
    bitcoind_path: str,
    btclib_node_python: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[BitcoindAdapter, BtclibNodeAdapter]]:
    """Yield one fresh `BitcoindAdapter` and one fresh `BtclibNodeAdapter`.

    [ISS 43](https://github.com/btclib-org/bitcoin-node-tests/issues/43)'s
    own "most valuable case": a cluster of two different kinds of node,
    started independently and never wired together by this fixture --
    matching `bitcoind_cluster` above, a test's own `connect_nodes` is
    what joins them. Both fixtures this depends on skip the whole module
    without their own node, so a test naming this one skips the same way
    rather than starting only one side of the pair.

    Function-scoped like `bitcoind_cluster`, not session-scoped like
    either adapter fixture above: a fresh chain and a fresh pair of ports
    per test, the same reason `bitcoind_cluster` gives for its own.

    Both adapters are constructed, and so both draw their ports, before
    either starts -- unlike `bitcoind_cluster`'s own loop, which starts
    each node before the next one draws its ports. `free_ports` reserves
    all four here in one call rather than as two pairs, which is what
    keeps this node's ports from landing on the other's.
    """
    rpc_port1, p2p_port1, rpc_port2, p2p_port2 = free_ports(4)
    bitcoind = BitcoindAdapter(
        bitcoind_path, tmp_path_factory.mktemp("bitcoind"), rpc_port1, p2p_port1
    )
    btclib_node = BtclibNodeAdapter(
        btclib_node_python,
        tmp_path_factory.mktemp("btclib-node"),
        rpc_port2,
        p2p_port2,
    )
    bitcoind.start()
    try:
        btclib_node.start()
    except BaseException:
        bitcoind.stop()
        raise
    try:
        yield bitcoind, btclib_node
    finally:
        try:
            btclib_node.stop()
        finally:
            bitcoind.stop()
