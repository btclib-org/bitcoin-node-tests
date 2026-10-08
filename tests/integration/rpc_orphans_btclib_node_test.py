# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_orphans`, rewritten on tf2's own harness: btclib-node.

`rpc_orphans_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.ORPHANAGE` is declared
where the build names `getorphantxs` (`btclib_node.py`'s own docstring):
each test is a counted skip on the released build and passes on `main`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_orphans_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_orphans_test import (
    getorphantxs_is_hidden_and_refuses_a_boolean_verbosity,
    getorphantxs_reports_each_orphan_and_its_announcers,
    orphans_leave_the_orphanage_with_their_parents,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_orphans_leave_the_orphanage_with_their_parents(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    orphans_leave_the_orphanage_with_their_parents(btclib_node_cluster, skip_counts)


def test_getorphantxs_reports_each_orphan_and_its_announcers(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getorphantxs_reports_each_orphan_and_its_announcers(
        btclib_node_cluster, skip_counts
    )


def test_getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
        btclib_node_cluster, skip_counts
    )
