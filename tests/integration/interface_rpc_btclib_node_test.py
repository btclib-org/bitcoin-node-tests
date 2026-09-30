# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_rpc`, rewritten on this harness: btclib-node.

`interface_rpc_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `btclib_node.py`'s own docstring has no build
declaring `Capability.RPC_INFO`, `Capability.GENERATE` or
`Capability.RPC_WORK_QUEUE`, so the `getrpcinfo` test, the notification
test past its requests that are no notification, and the work queue
test are counted skips. A run of the last on this node also needs
`waitfornewblock`, which `rpc/callbacks.py`'s own dispatch table does
not name on either build.

The batch and the status code tests ask for nothing beyond the node's
own RPC. A build before
[ISS btclib-node#1109](https://github.com/btclib-org/btclib-node/issues/1109)
answers every request in the JSON-RPC 2.0 envelope with HTTP 200 and
refuses a request with no `id`, so both fail there.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/interface_rpc_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_getrpcinfo_names_the_call_running_and_the_log(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: `getrpcinfo`, over btclib-node."""
    getrpcinfo_names_the_call_running_and_the_log(btclib_node_cluster, skip_counts)


def test_a_batch_is_answered_member_by_member(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a batch in each JSON-RPC version, over btclib-node."""
    a_batch_is_answered_member_by_member(btclib_node_cluster, skip_counts)


def test_each_version_is_answered_with_its_own_status(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: each version's HTTP status, over btclib-node."""
    each_version_is_answered_with_its_own_status(btclib_node_cluster, skip_counts)


def test_a_notification_runs_and_is_answered_with_no_content(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a 2.0 notification's 204, over btclib-node."""
    a_notification_runs_and_is_answered_with_no_content(
        btclib_node_cluster, skip_counts
    )


def test_a_full_work_queue_refuses_the_request_beyond_it(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: a full work queue's 503, over btclib-node."""
    a_full_work_queue_refuses_the_request_beyond_it(btclib_node_cluster, skip_counts)
