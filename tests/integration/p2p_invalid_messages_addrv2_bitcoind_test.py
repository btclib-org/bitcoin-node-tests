# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, its four `addrv2` checks: bitcoind.

Read from Core's `test/functional/p2p_invalid_messages.py`:
`p2p_invalid_messages_addrv2_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
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
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    addrv2_empty_keeps_the_connection(bitcoind_adapter)


def test_addrv2_empty_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    addrv2_empty_is_logged(bitcoind_adapter, skip_counts)


def test_addrv2_no_addresses_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    addrv2_no_addresses_keeps_the_connection(bitcoind_adapter)


def test_addrv2_no_addresses_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    addrv2_no_addresses_is_logged(bitcoind_adapter, skip_counts)


def test_addrv2_too_long_address_keeps_the_connection(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    addrv2_too_long_address_keeps_the_connection(bitcoind_adapter)


def test_addrv2_too_long_address_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    addrv2_too_long_address_is_logged(bitcoind_adapter, skip_counts)


def test_addrv2_unrecognized_network_keeps_the_connection(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    addrv2_unrecognized_network_keeps_the_connection(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_addrv2_unrecognized_network_is_logged(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    addrv2_unrecognized_network_is_logged(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
