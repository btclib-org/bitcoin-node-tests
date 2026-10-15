# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same three checks: btclib-node.

`p2p_invalid_messages_dropped_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220); its own docstring is where the wire fact each of these
three asks for -- the connection survives a malformed message rather than being
dropped -- is argued. PyPI's `2026.10.8` and `main` keep it on all three.

`TF2.md`'s per-test table carries each test's verdict.

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
    """The target: the wire half the body module names, over btclib-node."""
    duplicate_version_keeps_the_connection(btclib_node_adapter)


def test_duplicate_version_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    duplicate_version_is_logged(btclib_node_adapter, skip_counts)


def test_wrong_checksum_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    wrong_checksum_keeps_the_connection(btclib_node_adapter)


def test_wrong_checksum_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    wrong_checksum_is_logged(btclib_node_adapter, skip_counts)


def test_invalid_msgtype_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    invalid_msgtype_keeps_the_connection(btclib_node_adapter)


def test_invalid_msgtype_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    invalid_msgtype_is_logged(btclib_node_adapter, skip_counts)
