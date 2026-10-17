# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_invalid_messages`, the same three checks: btcd.

`p2p_invalid_messages_dropped_test.py` beside this module is the body,
run here against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_invalid_messages_dropped_btcd_test.py
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
    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_duplicate_version_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    duplicate_version_keeps_the_connection(btcd_adapter)


def test_duplicate_version_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    duplicate_version_is_logged(btcd_adapter, skip_counts)


def test_wrong_checksum_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    wrong_checksum_keeps_the_connection(btcd_adapter)


def test_wrong_checksum_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    wrong_checksum_is_logged(btcd_adapter, skip_counts)


def test_invalid_msgtype_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    invalid_msgtype_keeps_the_connection(btcd_adapter)


def test_invalid_msgtype_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    invalid_msgtype_is_logged(btcd_adapter, skip_counts)
