# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_includeconf`, one body over either node.

Read from Core's `test/functional/feature_includeconf.py` (`fa71c15f8610`,
2025-11-26), the option and disk families together
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`includeconf=` in `bitcoin.conf` reads each file it names after the one
naming it, one named inside an included file is ignored with a warning,
one naming a missing file refuses the start, and `-includeconf` on the
command line refuses it too, each refusal and the warning in Core's own
words.

Each test builds its node over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since the files are
written there before the node starts. `bitcoin.conf` here holds only the
lines each test writes, in its default section: neither adapter writes a
`bitcoin.conf`, where Core's harness writes one and the test appends to
its `[regtest]` section. An `includeconf` in a chain's own section is a
case of its own for btclib-node,
[ISS btclib-node#1302](https://github.com/btclib-org/btclib-node/issues/1302).

The order is observed through `-uacomment`, as Core observes it: each
file names a comment, and `getnetworkinfo`'s subversion lists them in
the order the node read them (`Capability.UA_COMMENT`). That test runs
Core's steps whose subject is the order -- one file included, a second
named inside the first and ignored, then both named from `bitcoin.conf`
-- and every other test writes no `uacomment` line, its subject being a
refusal or a warning matched against the whole of the node's stderr, as
`assert_start_raises_init_error` and `stop_node`'s own `expected_stderr`
match by default. btclib-node, which registers no `-uacomment`, warns
about the unknown key on stderr, which those tests do not ask about. The
warning Core's `stop_node` expects after the nested step is the nested
test's to match, not the order test's.

Every refusal is Core's own `expected_msg`, matched against the stderr
of a start that exited with a code other than `0` before its RPC
answered (`node.py`'s own `_wait_for_rpc`). The warning is matched
against the stderr of a start that answered, read from the file
`NodeAdapter.start` redirects each start's stderr to, under the data
directory's own `stderr/`.

Core's own file comments out its check of an invalid key inside an
included file, and that check is not ported.

`feature_includeconf_bitcoind_test.py` and
`feature_includeconf_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "a_missing_included_file_is_refused",
    "a_nested_includeconf_is_ignored_with_a_warning",
    "includeconf_files_are_read_in_order",
    "includeconf_on_the_command_line_is_refused",
    "noincludeconf_0_on_the_command_line_is_refused",
]

# Core's own `expected_msg` for each refusal, and `expected_stderr`
_COMMAND_LINE_TRUE = (
    "Error: Error parsing command line arguments: -includeconf cannot be used "
    "from commandline; -includeconf=true"
)
_COMMAND_LINE_NAMED = (
    "Error: Error parsing command line arguments: -includeconf cannot be used "
    'from commandline; -includeconf="relative2.conf"'
)
_MISSING = (
    "Error: Error reading configuration file: Failed to include configuration "
    "file relative.conf"
)
_NESTED = (
    "warning: -includeconf cannot be used from included files; ignoring "
    "-includeconf=relative2.conf"
)

# `_wait_for_rpc`'s own wording (`node.py`), split into the exit code and
# the stderr it carries
_EARLY_EXIT = re.compile(
    r"node process exited with (-?\d+) before its RPC answered -- stderr: (.*)",
    re.DOTALL,
)

# the directory `NodeAdapter.start` redirects each start's stderr under
_STDERR_DIR = "stderr"


def _node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    datadir: Path,
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Return a node over `datadir`, not yet started, on ports of its own.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param datadir: the data directory the test writes its files into.
    """
    rpc_port, p2p_port = free_ports(2)
    return make_adapter(cls, executable, datadir, rpc_port, p2p_port)


def _write_bare_files(datadir: Path) -> None:
    """Write Core's files, less every `uacomment` line and less `relative.conf`.

    `relative.conf` is each test's own to write, or to leave missing.

    :param datadir: the data directory to write into.
    """
    datadir.mkdir()
    (datadir / "relative2.conf").write_text("")
    (datadir / "bitcoin.conf").write_text("includeconf=relative.conf\n")


def _refused_stderr(node: NodeAdapter, extra_args: list[str]) -> str:
    """Start `node` with `extra_args`, and return the stderr it exits with.

    Core's own `assert_start_raises_init_error`: the start fails, with an
    exit code other than `0`, before its RPC ever answers.

    :param node: a node not yet started.
    :param extra_args: what to start it with.
    """
    try:
        with pytest.raises(RuntimeError) as refused:
            node.restart(extra_args)
    finally:
        node.stop()
    early_exit = _EARLY_EXIT.fullmatch(str(refused.value))
    assert early_exit is not None
    assert int(early_exit[1]) != 0
    return early_exit[2].strip()


def _subversion(node: NodeAdapter) -> str:
    """Return `getnetworkinfo`'s own `subversion`."""
    info = node.rpc.call("getnetworkinfo")
    assert isinstance(info, dict)
    subversion = info["subversion"]
    assert isinstance(subversion, str)
    return subversion


def includeconf_files_are_read_in_order(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check each included file is read after its includer, a nested one never.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    datadir = tmp_path / "datadir"
    node = _node(make_adapter, cls, executable, datadir)
    require(Capability.UA_COMMENT, node.capabilities, skip_counts)
    datadir.mkdir()
    (datadir / "relative.conf").write_text("uacomment=relative\n")
    (datadir / "relative2.conf").write_text("uacomment=relative2\n")
    (datadir / "bitcoin.conf").write_text("uacomment=main\nincludeconf=relative.conf\n")
    try:
        node.start()
        assert _subversion(node).endswith("main; relative)/")

        with (datadir / "relative.conf").open("a") as relative:
            relative.write("includeconf=relative2.conf\n")
        node.restart()
        assert _subversion(node).endswith("main; relative)/")

        (datadir / "relative.conf").write_text("uacomment=relative\n")
        with (datadir / "bitcoin.conf").open("a") as bitcoin_conf:
            bitcoin_conf.write("includeconf=relative2.conf\n")
        node.restart()
        assert _subversion(node).endswith("main; relative; relative2)/")
    finally:
        node.stop()


def noincludeconf_0_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check `-noincludeconf=0`, a double negative, is refused as `true`.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    _write_bare_files(datadir)
    (datadir / "relative.conf").write_text("")
    node = _node(make_adapter, cls, executable, datadir)
    assert _refused_stderr(node, ["-noincludeconf=0"]) == _COMMAND_LINE_TRUE


def includeconf_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check `-includeconf=<file>` is refused, naming the first file given.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    _write_bare_files(datadir)
    (datadir / "relative.conf").write_text("")
    node = _node(make_adapter, cls, executable, datadir)
    refused = _refused_stderr(
        node, ["-includeconf=relative2.conf", "-includeconf=no_warn.conf"]
    )
    assert refused == _COMMAND_LINE_NAMED


def a_nested_includeconf_is_ignored_with_a_warning(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check an `includeconf` inside an included file starts, warning on stderr.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    _write_bare_files(datadir)
    (datadir / "relative.conf").write_text("includeconf=relative2.conf\n")
    node = _node(make_adapter, cls, executable, datadir)
    try:
        node.start()
    finally:
        node.stop()
    # the data directory is this test's own, and this its one start
    (stderr_file,) = (datadir / _STDERR_DIR).iterdir()
    assert stderr_file.read_text(encoding="utf-8").strip() == _NESTED


def a_missing_included_file_is_refused(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
) -> None:
    """Check an `includeconf` naming no file refuses the start.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    """
    datadir = tmp_path / "datadir"
    _write_bare_files(datadir)
    node = _node(make_adapter, cls, executable, datadir)
    assert _refused_stderr(node, []) == _MISSING
