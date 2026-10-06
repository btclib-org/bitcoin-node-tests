# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same four `addrv2` checks: btclib-node.

`p2p_invalid_messages_addrv2_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220); its own docstring is where the wire fact each of these
four asks for -- the connection survives a malformed `addrv2` -- is argued.

The wire halves need a `ping` queued behind the `addrv2` before it, as
[ISS btclib-node#1410](https://github.com/btclib-org/btclib-node/issues/1410)
made it. `TF2.md`'s per-test table carries each row's verdict for each
build.

The log half is not reached: this node's own `Logger` (`log.py`) writes
English, not Core's, so `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), and the log tests skip.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.p2p_invalid_messages_addrv2_test import (
    addrv2_empty_is_logged,
    addrv2_empty_keeps_the_connection,
    addrv2_no_addresses_is_logged,
    addrv2_no_addresses_keeps_the_connection,
    addrv2_too_long_address_is_logged,
    addrv2_too_long_address_keeps_the_connection,
    addrv2_unrecognized_network_is_logged,
    addrv2_unrecognized_network_keeps_the_connection,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_addrv2_empty_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    addrv2_empty_keeps_the_connection(btclib_node_adapter)


def test_addrv2_empty_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    addrv2_empty_is_logged(btclib_node_adapter, skip_counts)


def test_addrv2_no_addresses_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    addrv2_no_addresses_keeps_the_connection(btclib_node_adapter)


def test_addrv2_no_addresses_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    addrv2_no_addresses_is_logged(btclib_node_adapter, skip_counts)


def test_addrv2_too_long_address_keeps_the_connection(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    addrv2_too_long_address_keeps_the_connection(btclib_node_adapter)


def test_addrv2_too_long_address_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    addrv2_too_long_address_is_logged(btclib_node_adapter, skip_counts)


def test_addrv2_unrecognized_network_keeps_the_connection(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    addrv2_unrecognized_network_keeps_the_connection(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_addrv2_unrecognized_network_is_logged(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btclib-node."""
    addrv2_unrecognized_network_is_logged(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
