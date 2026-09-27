# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_orphans`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/rpc_orphans.py`: `rpc_orphans_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_orphans_leave_the_orphanage_with_their_parents(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    orphans_leave_the_orphanage_with_their_parents(bitcoind_cluster, skip_counts)


def test_getorphantxs_reports_each_orphan_and_its_announcers(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getorphantxs_reports_each_orphan_and_its_announcers(bitcoind_cluster, skip_counts)


def test_getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
        bitcoind_cluster, skip_counts
    )
