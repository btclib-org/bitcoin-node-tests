# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_rpc`, rewritten on this harness: florestad.

`interface_rpc_test.py` beside this module is the body, run here against
florestad, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). florestad has neither `-rpcworkqueue` nor
`generatetoaddress`, so it declares neither `Capability.RPC_WORK_QUEUE`
nor `Capability.GENERATE`. The work queue test is a counted skip, and so
is the notification test past its requests that are no notification,
once those pass.

These fail against `v0.9.1`, each on florestad's own answer:

- the batch test: florestad reads a body as one request object, and
  refuses a batch, an empty one included, with HTTP 400;
- the status code test: florestad answers an unknown method with
  `-32600`, Core's `RPC_INVALID_REQUEST`, where Core answers `-32601`;
- the notification test: florestad refuses a request without `params`
  with HTTP 400 ("missing field `params`").

    export TF2_INTEGRATION=1 TF2_FLORESTAD=<florestad>
    uv run pytest tests/integration/interface_rpc_florestad_test.py
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

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.florestad import FlorestadAdapter

pytestmark = pytest.mark.integration


def test_getrpcinfo_names_the_call_running_and_the_log(
    florestad_cluster: Callable[[int], list[FlorestadAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: `getrpcinfo`, over florestad."""
    getrpcinfo_names_the_call_running_and_the_log(florestad_cluster, skip_counts)


def test_a_batch_is_answered_member_by_member(
    florestad_cluster: Callable[[int], list[FlorestadAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a batch in each JSON-RPC version, over florestad."""
    a_batch_is_answered_member_by_member(florestad_cluster, skip_counts)


def test_each_version_is_answered_with_its_own_status(
    florestad_cluster: Callable[[int], list[FlorestadAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: each version's HTTP status, over florestad."""
    each_version_is_answered_with_its_own_status(florestad_cluster, skip_counts)


def test_a_notification_runs_and_is_answered_with_no_content(
    florestad_cluster: Callable[[int], list[FlorestadAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a 2.0 notification's 204, over florestad."""
    a_notification_runs_and_is_answered_with_no_content(florestad_cluster, skip_counts)


def test_a_full_work_queue_refuses_the_request_beyond_it(
    florestad_cluster: Callable[[int], list[FlorestadAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a full work queue's 503, over florestad."""
    a_full_work_queue_refuses_the_request_beyond_it(florestad_cluster, skip_counts)
