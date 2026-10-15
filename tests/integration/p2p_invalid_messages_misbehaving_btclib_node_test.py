# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same checks: btclib-node.

`p2p_invalid_messages_misbehaving_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220); its own docstring is where the Core checks it
splits into a wire half and a log half are argued.

The wire half is the same fact on this node too, on PyPI's `2026.10.8` and
on `main` (`afd4c584`) alike. The `inv`, `getdata` and `headers` callbacks
(`p2p/callbacks.py`) each call `_refuse_past_bound` before parsing, and
`BlockIndex._validate_header_batch` (`chainstate/block_index.py`) goes through
`_assert_valid_pow` and `_assert_continuous`. Each raises `MisbehavingError`,
which `_drop` (`p2p/main.py`) hands to
`P2pManager.maybe_discourage_and_disconnect`.

The log half is not: this node's own `Logger` (`log.py`) writes English,
not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and every log check skips.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
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
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_inv_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    oversized_inv_disconnects_the_peer(btclib_node_adapter)


def test_oversized_inv_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_inv_is_logged(btclib_node_adapter, skip_counts)


def test_oversized_getdata_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    oversized_getdata_disconnects_the_peer(btclib_node_adapter)


def test_oversized_getdata_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_getdata_is_logged(btclib_node_adapter, skip_counts)


def test_oversized_headers_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    oversized_headers_disconnects_the_peer(btclib_node_adapter)


def test_oversized_headers_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    oversized_headers_is_logged(btclib_node_adapter, skip_counts)


def test_invalid_pow_header_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    invalid_pow_header_disconnects_the_peer(btclib_node_adapter)


def test_invalid_pow_header_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    invalid_pow_header_is_logged(btclib_node_adapter, skip_counts)


def test_noncontinuous_headers_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    noncontinuous_headers_disconnects_the_peer(btclib_node_adapter, skip_counts)


def test_noncontinuous_headers_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    noncontinuous_headers_is_logged(btclib_node_adapter, skip_counts)
