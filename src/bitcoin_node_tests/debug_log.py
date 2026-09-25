# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`assert_debug_log`: wait for a node's own log to carry a fact.

Core's own `TestNode.assert_debug_log`
(`test/functional/test_framework/test_node.py`): a context manager
recording the log file's own size at entry, and waiting up to `timeout`
after the block exits for every expected substring to have appeared in
whatever was appended since. `Capability.DEBUG_LOG` (`capability.py`) is
what gates a caller reaching this at all -- only `BitcoindAdapter`
(`bitcoind.py`) names a `debug_log_path` today, so a test importing this
module is one whose own `require` call has already run, rather than
this function gating the same capability a second time.
"""

from __future__ import annotations

import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from bitcoin_node_tests.timeout_factor import scaled

__all__ = [
    "assert_debug_log",
]

_POLL_INTERVAL = 0.1


@contextmanager
def assert_debug_log(
    log_path: Path, expected_substrings: Sequence[str], *, timeout: float = 10.0
) -> Iterator[None]:
    """Yield, then wait for every one of `expected_substrings` to appear.

    :param log_path: the node's own debug log,
        `BitcoindAdapter.debug_log_path`.
    :param expected_substrings: every substring the block's own action is
        expected to have caused; checked against what the log gained
        since this context was entered, not against the whole file, so
        an earlier, unrelated line carrying the same words does not pass
        this.
    :param timeout: how long to keep polling after the block exits,
        before `--timeout-factor`'s own scaling (`timeout_factor.scaled`).
    :raises AssertionError: some substring never appeared within
        `timeout`.
    """
    timeout = scaled(timeout)
    start_size = log_path.stat().st_size if log_path.exists() else 0
    yield
    deadline = time.monotonic() + timeout
    remaining = list(expected_substrings)
    appended = ""
    while remaining and time.monotonic() < deadline:
        with log_path.open(encoding="utf-8", errors="replace") as log_file:
            log_file.seek(start_size)
            appended = log_file.read()
        remaining = [s for s in expected_substrings if s not in appended]
        if remaining:
            time.sleep(_POLL_INTERVAL)
    if remaining:
        msg = f"{remaining!r} not found in the log appended since entry:\n{appended}"
        raise AssertionError(msg)
