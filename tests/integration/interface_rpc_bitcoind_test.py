# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_rpc`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/interface_rpc.py`:
`interface_rpc_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.interface_rpc_test import (
    a_batch_is_answered_member_by_member,
    a_full_work_queue_refuses_the_request_beyond_it,
    a_notification_runs_and_is_answered_with_no_content,
    each_version_is_answered_with_its_own_status,
    getrpcinfo_names_the_call_running_and_the_log,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_getrpcinfo_names_the_call_running_and_the_log(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `getrpcinfo`, over bitcoind."""
    getrpcinfo_names_the_call_running_and_the_log(bitcoind_cluster, skip_counts)


def test_a_batch_is_answered_member_by_member(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a batch in each JSON-RPC version, over bitcoind."""
    a_batch_is_answered_member_by_member(bitcoind_cluster, skip_counts)


def test_each_version_is_answered_with_its_own_status(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: each version's HTTP status, over bitcoind."""
    each_version_is_answered_with_its_own_status(bitcoind_cluster, skip_counts)


def test_a_notification_runs_and_is_answered_with_no_content(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a 2.0 notification's 204, over bitcoind."""
    a_notification_runs_and_is_answered_with_no_content(bitcoind_cluster, skip_counts)


def test_a_full_work_queue_refuses_the_request_beyond_it(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a full work queue's 503, over bitcoind."""
    a_full_work_queue_refuses_the_request_beyond_it(bitcoind_cluster, skip_counts)
