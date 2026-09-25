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
    from collections.abc import Iterator

# one tally for the whole session, shared by every fixture and test
# below: `pytest_sessionfinish` prints it once, rather than once per
# node this session happened to drive
_skip_counts = SkipCounts()


@pytest.fixture(scope="session")
def skip_counts() -> SkipCounts:
    """Return this session's own tally, shared by every test that skips."""
    return _skip_counts


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Print the session's skip tally where a bare run still shows it.

    A fixture's own teardown print is captured with everything else a
    test writes and shown only where that test failed; this hook runs
    once the whole session is over and is not subject to that capture --
    rule 4's "the run prints a skip count" needs that, a green run that
    skipped every `Capability.MINE` case otherwise printing nothing at
    all.

    :param session: unused; the hook's own signature names it.
    :param exitstatus: unused; the hook's own signature names it.
    """
    del session, exitstatus
    print(_skip_counts.report())  # noqa: T201


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
