# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same four `addrv2` checks: btcd.

`p2p_invalid_messages_addrv2_test.py` beside this module is the body,
run here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_invalid_messages_addrv2_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
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
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    addrv2_empty_keeps_the_connection(btcd_adapter)


def test_addrv2_empty_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btcd."""
    addrv2_empty_is_logged(btcd_adapter, skip_counts)


def test_addrv2_no_addresses_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    addrv2_no_addresses_keeps_the_connection(btcd_adapter)


def test_addrv2_no_addresses_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btcd."""
    addrv2_no_addresses_is_logged(btcd_adapter, skip_counts)


def test_addrv2_too_long_address_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    addrv2_too_long_address_keeps_the_connection(btcd_adapter)


def test_addrv2_too_long_address_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the log half the body module names, over btcd."""
    addrv2_too_long_address_is_logged(btcd_adapter, skip_counts)


def test_addrv2_unrecognized_network_keeps_the_connection(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    addrv2_unrecognized_network_keeps_the_connection(
        make_adapter, BtcdAdapter, btcd_path, tmp_path
    )


def test_addrv2_unrecognized_network_is_logged(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    addrv2_unrecognized_network_is_logged(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
