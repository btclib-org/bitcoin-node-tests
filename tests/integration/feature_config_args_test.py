# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_config_args`, the steps whose subject is a proxy option.

Read from Core's `test/functional/feature_config_args.py`
(`2630d8e6c9d6`, 2026-09-22), a file of
[ISS 47](https://github.com/btclib-org/bitcoin-node-tests/issues/47):
`-proxy` given no value is refused (`test_invalid_command_line_options`),
`-connect` ignores `-seednode`, and `-dnsseed` too where a proxy is given
(`test_connect_with_seednode`), and `-privatebroadcast` is refused without
a Tor or I2P proxy or beside `-connect`, and warns beside
`-proxyrandomize=0` (`test_privatebroadcast`). The file's other steps are
not ported here: they are
[ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
log and configuration file steps, the proxy in them only keeping the node
off the network.

No step reads what the node asks of a proxy: each refuses a start, reads a
line of the log, or reads the stderr of a start, so no
`socks5.Socks5Proxy` runs.
Each step asks for `Capability.PROXY`; the second also for
`Capability.DEBUG_LOG`, `Capability.DNS_SEED` and
`Capability.ADDRESS_FETCH`, and the third for
`Capability.PRIVATE_BROADCAST`.

What differs from Core's file:

- Core's `write_config` (`test_framework/util.py`) writes `dnsseed=0`
  into `bitcoin.conf`, which neither adapter writes. The starts given
  `-seednode` pass it as `-dnsseed=0`; the others leave it out.
- Core's step also asserts `-connect` soft-disables `-listen`, which is
  logged only where nothing else sets `-listen`. `BitcoindAdapter` passes
  `-bind`, which sets it, so only the `-dnsseed` line is asserted.
- Core's warning of the last step ends "To reduce this risk, set
  -proxyrandomize=1." from bitcoin/bitcoin@2630d8e6c9d6 on, and "For
  maximum privacy set -proxyrandomize=1." before it. The build's `-help`
  tells them apart (`_scopes_its_claims`), and the step asserts that
  build's own sentence.
- Core reads the stderr of its `stop_node` where the warning of the last
  step is given. Here that is the file `NodeAdapter.start` redirects the
  start's stderr to, as `feature_includeconf_test.py` reads it.

`feature_config_args_bitcoind_test.py` and
`feature_config_args_btclib_node_test.py` run each body,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.debug_log import assert_debug_log
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

__all__ = [
    "a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy",
    "a_proxy_without_a_value_is_refused",
    "private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing",
]

# Core's `UNREACHABLE_PROXY_ARG` (`test_framework/netutil.py`)
_UNREACHABLE_PROXY = "-proxy=127.0.0.1:1"

# `write_config`'s own `dnsseed=0` line (`test_framework/util.py`)
_NO_DNSSEED = "-dnsseed=0"

_PROXY_WITHOUT_VALUE = (
    "Error: Error parsing command line arguments: Can not set -proxy with "
    "no value. Please specify value with -proxy=value."
)

_SEEDNODE_IGNORED = "-seednode is ignored when -connect is used\n"
_DNSSEED_IGNORED = "-dnsseed is ignored when -connect is used and -proxy is specified\n"
_ADDCON_THREAD = "addcon thread start\n"
_DNSSEED_DISABLED = (
    "parameter interaction: -connect or -maxconnections=0 set -> setting -dnsseed=0"
)

_NO_TOR_OR_I2P = (
    "Error: Private broadcast of own transactions requested (-privatebroadcast), "
    "but none of Tor or I2P networks is reachable"
)
_WITH_CONNECT = (
    "Error: Private broadcast of own transactions requested (-privatebroadcast), "
    "but -connect is also configured. They are incompatible because the private "
    "broadcast needs to open new connections to randomly chosen Tor or I2P "
    "peers. Consider using -maxconnections=0 -addnode=... instead"
)
_NOT_RANDOMIZED = (
    "Warning: Private broadcast of own transactions requested (-privatebroadcast) "
    "and -proxyrandomize is disabled. Tor circuits for private broadcast "
    "connections may be correlated to other connections over Tor. "
)
_RISK_REDUCED = "To reduce this risk, set -proxyrandomize=1."
_MAXIMUM_PRIVACY = "For maximum privacy set -proxyrandomize=1."

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
    tmp_path: Path,
    skip_counts: SkipCounts,
    capabilities: Sequence[Capability],
) -> BitcoindAdapter | BtclibNodeAdapter:
    """Return a node not yet started, having asked it for `capabilities`.

    :param capabilities: what the step needs, each asked of the node.
    """
    rpc_port, p2p_port = free_ports(2)
    node = make_adapter(cls, executable, tmp_path / "node", rpc_port, p2p_port)
    for capability in capabilities:
        require(capability, node.capabilities, skip_counts)
    return node


def _refused_stderr(node: NodeAdapter, extra_args: Sequence[str]) -> str:
    """Start `node` with `extra_args`, and return the stderr it exits with.

    Core's own `assert_start_raises_init_error`: the start fails, with an
    exit code other than `0`, before its RPC ever answers.
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


@lru_cache
def _scopes_its_claims(executable: str) -> bool:
    """Return whether `executable` words its private broadcast claims as risk.

    bitcoin/bitcoin@2630d8e6c9d6 reworded the `-proxyrandomize`
    warning's last sentence and added "best-effort concealment" to
    `-privatebroadcast`'s `-help` text, which is what this reads: no build
    lists the sentence and words the warning the old way, or the reverse.

    :param executable: the `bitcoind` binary to probe.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-help", "-nosettings"], check=False, capture_output=True
    )
    return b"best-effort concealment" in b" ".join(probe.stdout.split())


def _debug_log(node: BitcoindAdapter | BtclibNodeAdapter) -> Path:
    """Return the log Core's own lines are read from.

    :raises TypeError: `node` declares `Capability.DEBUG_LOG` without
        being the adapter that names a `debug_log_path`.
    """
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares DEBUG_LOG, naming no debug.log"
        raise TypeError(err_msg)
    return node.debug_log_path


def a_proxy_without_a_value_is_refused(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-proxy` with no value refuses the start, naming the fix.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    node = _node(
        make_adapter, cls, executable, tmp_path, skip_counts, (Capability.PROXY,)
    )
    assert _refused_stderr(node, ["-proxy"]) == _PROXY_WITHOUT_VALUE


def a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check what `-connect`, and `-noconnect`, ignore, and what they log.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    capabilities = (
        Capability.PROXY,
        Capability.DEBUG_LOG,
        Capability.DNS_SEED,
        Capability.ADDRESS_FETCH,
    )
    node = _node(make_adapter, cls, executable, tmp_path, skip_counts, capabilities)
    log_path = _debug_log(node)
    try:
        # `-connect` ignores `-seednode`
        with assert_debug_log(log_path, [_SEEDNODE_IGNORED]):
            node.restart(
                [
                    "-connect=fakeaddress1",
                    "-seednode=fakeaddress2",
                    _NO_DNSSEED,
                    _UNREACHABLE_PROXY,
                ]
            )

        # and `-dnsseed`, where a proxy is given
        with assert_debug_log(log_path, [_DNSSEED_IGNORED]):
            node.restart(["-connect=fakeaddress1", "-dnsseed=1", _UNREACHABLE_PROXY])

        # `-dnsseed` soft-disabled by `-connect` is not a setting ignored
        with assert_debug_log(
            log_path, [_ADDCON_THREAD], [_DNSSEED_IGNORED], timeout=2
        ):
            node.restart(["-connect=fakeaddress1", _UNREACHABLE_PROXY])

        # a `-connect` given only to disable it ignores nothing, and
        # soft-disables `-dnsseed` all the same
        for connect_arg in ["-connect=0", "-noconnect"]:
            with assert_debug_log(
                log_path, [_ADDCON_THREAD], [_SEEDNODE_IGNORED], timeout=2
            ):
                node.restart([connect_arg, "-seednode=fakeaddress2", _NO_DNSSEED])
            with assert_debug_log(log_path, [_DNSSEED_DISABLED]):
                node.restart([connect_arg])
            with assert_debug_log(log_path, [_DNSSEED_IGNORED]):
                node.restart([connect_arg, "-dnsseed", "-proxy=localhost:1080"])
    finally:
        node.stop()


def private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check `-privatebroadcast`'s two refusals and its warning.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: where the node's own data directory goes.
    :param skip_counts: the session's own tally.
    """
    capabilities = (Capability.PROXY, Capability.PRIVATE_BROADCAST)
    node = _node(make_adapter, cls, executable, tmp_path, skip_counts, capabilities)
    stderr_dir = tmp_path / "node" / _STDERR_DIR
    onion = "-onion=127.0.0.1:9050"
    # none of Tor or I2P reachable at startup
    assert _refused_stderr(node, ["-privatebroadcast"]) == _NO_TOR_OR_I2P
    # incompatible with `-connect`
    refused = _refused_stderr(
        node, ["-privatebroadcast", "-connect=127.0.0.1:8333", onion]
    )
    assert refused == _WITH_CONNECT
    # allowed, but `-proxyrandomize=0` warns
    before = set(stderr_dir.iterdir())
    try:
        node.restart(["-privatebroadcast", onion, "-proxyrandomize=0"])
    finally:
        node.stop()
    (stderr_file,) = set(stderr_dir.iterdir()) - before
    last_sentence = (
        _RISK_REDUCED if _scopes_its_claims(executable) else _MAXIMUM_PRIVACY
    )
    warning = stderr_file.read_text(encoding="utf-8").strip()
    assert warning == _NOT_RANDOMIZED + last_sentence
