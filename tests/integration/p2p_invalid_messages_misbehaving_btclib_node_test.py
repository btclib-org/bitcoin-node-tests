# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same four checks: btclib-node.

`p2p_invalid_messages_misbehaving_test.py` beside this module is the body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220); its own docstring is where the four Core checks it
splits into a wire half and a log half are argued.

The wire half is the same fact on this node too, reached one way on PyPI's
`2026.9.24` and another on `main`. On the released build, the `getdata` and
`headers` callbacks (`p2p/callbacks.py`) hand the message to `GetData.parse`
and `Headers.parse`, which refuse a count over its own bound, and
`BlockIndex._validate_header_batch` (`chainstate/block_index.py`) calls
`BlockHeader.assert_valid_pow`; each refusal is a `BTClibException`, for which
`handle_p2p` (`p2p/main.py`) discourages the peer and stops the connection. On
`main`, the `inv`, `getdata` and `headers` callbacks each call
`_refuse_past_bound` before parsing, and `_validate_header_batch` goes through
`_assert_valid_pow`; both raise `MisbehavingError`, which `_drop`
(`p2p/main.py`) hands to `P2pManager.maybe_discourage_and_disconnect`, any
other `BTClibException` leaving the peer connected.

The log half is not: this node's own `Logger` (`log.py`) writes English,
not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and all four log checks skip.

`test_oversized_inv_disconnects_the_peer` is expected to fail on the
released build rather than to pass or to skip -- neither an `xfail` nor a
`pytest.skip.Exception` -- so this keeps reproducing [ISS
btclib-node#1145](https://github.com/btclib-org/btclib-node/issues/1145)
rather than hiding it: the released build's `inv` callback returns before
calling `Inv.parse` at all while `node.status < NodeStatus.BlockSynced`, a
status this adapter's own lone, peerless node never advances past, so an
oversized `inv` is dropped unread rather than refused. The other three wire
checks have no such guard in front of them, and pass on both builds, as
`test_oversized_inv_disconnects_the_peer` does on `main`. `TF2.md`'s per-test
table carries the verdict this failure is, not a decoration on this module.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
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
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_oversized_inv_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: fails on the released build (ISS btclib-node#1145)."""
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
