# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak`, rewritten on tf2's own harness: btcd.

`p2p_leak_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_leak_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_leak_test import (
    feature_negotiation_starts_at_the_wtxid_version,
    obsolete_version_disconnects_the_peer,
    obsolete_version_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_obsolete_version_disconnects_the_peer(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    obsolete_version_disconnects_the_peer(btcd_adapter)


def test_obsolete_version_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    obsolete_version_is_logged(btcd_adapter, skip_counts)


def test_feature_negotiation_starts_at_the_wtxid_version(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the version boundary the body module names."""
    feature_negotiation_starts_at_the_wtxid_version(btcd_adapter)
