# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same three checks: btclib-node.

`p2p_invalid_messages_dropped_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220); its own docstring is where the wire fact each of these
three asks for -- the connection survives a malformed message rather than being
dropped -- is argued. PyPI's `2026.9.24` does not keep it: every one of the
three reaches `P2pManager.discourage` and a `stop()`, one layer or another,
where Core only logs and continues. `main` keeps it for all three.

`test_wrong_checksum_keeps_the_connection` and
`test_invalid_msgtype_keeps_the_connection` are one mechanism on the released
build, measured live: `Connection.run`'s own `except Exception` around
`parse_messages` (`connection.py`) discourages and stops on *any*
`BTClibException` out of `frame_message`, and
`btclib.p2p.message._command_from_bytes` raises one for an invalid command
exactly the way `Message.parse`'s own checksum check does -- so a bad checksum
and an invalid message type take the same branch to the same outcome. [ISS
btclib-node#1130](https://github.com/btclib-org/btclib-node/issues/1130) names
the checksum case; this reproduces both by the same measurement, no second issue
needed for the second branch of one handler.

`test_duplicate_version_keeps_the_connection` is a different mechanism there:
`handle_p2p_handshake`'s own dispatch (`p2p/main.py`) discourages and stops a
`version`/`verack`/`wtxidrelay`/`sendaddrv2` that arrives once the
connection is already `Connected`, before the `version` callback's own
"if `conn.version_message` is not `None`: return" guard is ever reached
-- the guard is live only for a repeat sent ahead of this node's own
`verack`, not after it, which is where Core's own test and this one send
theirs.
[ISS btclib-node#1133](https://github.com/btclib-org/btclib-node/issues/1133)
names it.

Each `*_keeps_the_connection` test below runs the body its bitcoind
counterpart runs, and is expected to fail on the released build rather than
to pass or to skip -- neither an `xfail` nor a `pytest.skip.Exception` -- so
this keeps reproducing the two issues above rather than hiding them, the
same convention `p2p_invalid_messages_misbehaving_btclib_node_test.py`
already holds for [ISS
btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145).
`TF2.md`'s per-test table carries the verdict these three failures are.

The log half is not reached by any of this: this node's own `Logger`
(`log.py`) writes English, not Core's, so `Capability.DEBUG_LOG` is not
declared (`btclib_node.py`'s own `capabilities`), and all three log tests
skip regardless of what the wire half above found.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_invalid_messages_dropped_test import (
    duplicate_version_is_logged,
    duplicate_version_keeps_the_connection,
    invalid_msgtype_is_logged,
    invalid_msgtype_keeps_the_connection,
    wrong_checksum_is_logged,
    wrong_checksum_keeps_the_connection,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_duplicate_version_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build (ISS btclib-node#1133)."""
    duplicate_version_keeps_the_connection(btclib_node_adapter)


def test_duplicate_version_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    duplicate_version_is_logged(btclib_node_adapter, skip_counts)


def test_wrong_checksum_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build (ISS btclib-node#1130)."""
    wrong_checksum_keeps_the_connection(btclib_node_adapter)


def test_wrong_checksum_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    wrong_checksum_is_logged(btclib_node_adapter, skip_counts)


def test_invalid_msgtype_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build, as ISS btclib-node#1130."""
    invalid_msgtype_keeps_the_connection(btclib_node_adapter)


def test_invalid_msgtype_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    invalid_msgtype_is_logged(btclib_node_adapter, skip_counts)
