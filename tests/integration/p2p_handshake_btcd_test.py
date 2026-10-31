# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_handshake`, rewritten on tf2's own harness: btcd.

`p2p_handshake_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_handshake_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_handshake_test import (
    feeler_completion_is_logged,
    feeler_is_dropped_after_its_version,
    limited_peer_is_kept_only_near_the_tip,
    limited_peer_refusal_is_logged,
    outbound_services_decide_the_connection,
    outbound_services_refusal_is_logged,
    redundant_verack_is_logged,
    redundant_verack_keeps_the_connection,
    self_connection_is_dropped,
    self_connection_is_logged,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_redundant_verack_keeps_the_connection(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    redundant_verack_keeps_the_connection(btcd_adapter)


def test_redundant_verack_is_logged(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    redundant_verack_is_logged(btcd_adapter, skip_counts)


def test_outbound_services_decide_the_connection(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    outbound_services_decide_the_connection(btcd_cluster, skip_counts)


def test_outbound_services_refusal_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    outbound_services_refusal_is_logged(btcd_cluster, skip_counts)


def test_limited_peer_is_kept_only_near_the_tip(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    limited_peer_is_kept_only_near_the_tip(btcd_cluster, skip_counts)


def test_limited_peer_refusal_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    limited_peer_refusal_is_logged(btcd_cluster, skip_counts)


def test_feeler_is_dropped_after_its_version(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    feeler_is_dropped_after_its_version(btcd_cluster, skip_counts)


def test_feeler_completion_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    feeler_completion_is_logged(btcd_cluster, skip_counts)


def test_self_connection_is_dropped(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the wire half the body module names, over btcd."""
    self_connection_is_dropped(btcd_cluster, skip_counts)


def test_self_connection_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the log half the body module names, over btcd."""
    self_connection_is_logged(btcd_cluster, skip_counts)
