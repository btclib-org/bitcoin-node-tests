# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, three checks it drops instead: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`:
`p2p_invalid_messages_dropped_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_duplicate_version_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    duplicate_version_keeps_the_connection(bitcoind_adapter)


def test_duplicate_version_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    duplicate_version_is_logged(bitcoind_adapter, skip_counts)


def test_wrong_checksum_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    wrong_checksum_keeps_the_connection(bitcoind_adapter)


def test_wrong_checksum_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    wrong_checksum_is_logged(bitcoind_adapter, skip_counts)


def test_invalid_msgtype_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    invalid_msgtype_keeps_the_connection(bitcoind_adapter)


def test_invalid_msgtype_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    invalid_msgtype_is_logged(bitcoind_adapter, skip_counts)
