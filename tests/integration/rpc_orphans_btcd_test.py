# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_orphans`, rewritten on tf2's own harness: btcd.

`rpc_orphans_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_orphans_btcd_test.py
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

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_orphans_leave_the_orphanage_with_their_parents(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    orphans_leave_the_orphanage_with_their_parents(btcd_cluster, skip_counts)


def test_getorphantxs_reports_each_orphan_and_its_announcers(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getorphantxs_reports_each_orphan_and_its_announcers(btcd_cluster, skip_counts)


def test_getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    getorphantxs_is_hidden_and_refuses_a_boolean_verbosity(btcd_cluster, skip_counts)
