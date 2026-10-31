# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_rpc`, rewritten on tf2's own harness: btcd.

`interface_rpc_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/interface_rpc_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_getrpcinfo_names_the_call_running_and_the_log(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: `getrpcinfo`, over btcd."""
    getrpcinfo_names_the_call_running_and_the_log(btcd_cluster, skip_counts)


def test_a_batch_is_answered_member_by_member(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a batch in each JSON-RPC version, over btcd."""
    a_batch_is_answered_member_by_member(btcd_cluster, skip_counts)


def test_each_version_is_answered_with_its_own_status(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: each version's HTTP status, over btcd."""
    each_version_is_answered_with_its_own_status(btcd_cluster, skip_counts)


def test_a_notification_runs_and_is_answered_with_no_content(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a 2.0 notification's 204, over btcd."""
    a_notification_runs_and_is_answered_with_no_content(btcd_cluster, skip_counts)


def test_a_full_work_queue_refuses_the_request_beyond_it(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a full work queue's 503, over btcd."""
    a_full_work_queue_refuses_the_request_beyond_it(btcd_cluster, skip_counts)
