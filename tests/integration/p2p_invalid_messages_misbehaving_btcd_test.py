# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_invalid_messages`, the same checks: btcd.

`p2p_invalid_messages_misbehaving_test.py` beside this module is the
body, run here against btcd, a target rather than the oracle (rule 3 of
issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration \
        -k p2p_invalid_messages_misbehaving_btcd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_invalid_messages_misbehaving_test import (
    invalid_pow_header_disconnects_the_peer,
    invalid_pow_header_is_logged,
    noncontinuous_headers_disconnects_the_peer,
    noncontinuous_headers_is_logged,
    oversized_getdata_disconnects_the_peer,
    oversized_getdata_is_logged,
    oversized_headers_disconnects_the_peer,
    oversized_headers_is_logged,
    oversized_inv_disconnects_the_peer,
    oversized_inv_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_inv_disconnects_the_peer(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    oversized_inv_disconnects_the_peer(btcd_adapter)


def test_oversized_inv_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_inv_is_logged(btcd_adapter, skip_counts)


def test_oversized_getdata_disconnects_the_peer(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    oversized_getdata_disconnects_the_peer(btcd_adapter)


def test_oversized_getdata_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_getdata_is_logged(btcd_adapter, skip_counts)


def test_oversized_headers_disconnects_the_peer(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    oversized_headers_disconnects_the_peer(btcd_adapter)


def test_oversized_headers_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_headers_is_logged(btcd_adapter, skip_counts)


def test_invalid_pow_header_disconnects_the_peer(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    invalid_pow_header_disconnects_the_peer(btcd_adapter)


def test_invalid_pow_header_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    invalid_pow_header_is_logged(btcd_adapter, skip_counts)


def test_noncontinuous_headers_disconnects_the_peer(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the wire half the body module names, over btcd."""
    noncontinuous_headers_disconnects_the_peer(btcd_adapter, skip_counts)


def test_noncontinuous_headers_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    noncontinuous_headers_is_logged(btcd_adapter, skip_counts)
