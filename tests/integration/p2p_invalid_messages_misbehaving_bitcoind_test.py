# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, four more of its own checks: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`:
`p2p_invalid_messages_misbehaving_test.py` beside this module is the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_invalid_messages_misbehaving_test import (
    invalid_pow_header_disconnects_the_peer,
    invalid_pow_header_is_logged,
    oversized_getdata_disconnects_the_peer,
    oversized_getdata_is_logged,
    oversized_headers_disconnects_the_peer,
    oversized_headers_is_logged,
    oversized_inv_disconnects_the_peer,
    oversized_inv_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_inv_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    oversized_inv_disconnects_the_peer(bitcoind_adapter)


def test_oversized_inv_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    oversized_inv_is_logged(bitcoind_adapter, skip_counts)


def test_oversized_getdata_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    oversized_getdata_disconnects_the_peer(bitcoind_adapter)


def test_oversized_getdata_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    oversized_getdata_is_logged(bitcoind_adapter, skip_counts)


def test_oversized_headers_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    oversized_headers_disconnects_the_peer(bitcoind_adapter)


def test_oversized_headers_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    oversized_headers_is_logged(bitcoind_adapter, skip_counts)


def test_invalid_pow_header_disconnects_the_peer(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    invalid_pow_header_disconnects_the_peer(bitcoind_adapter)


def test_invalid_pow_header_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    invalid_pow_header_is_logged(bitcoind_adapter, skip_counts)
