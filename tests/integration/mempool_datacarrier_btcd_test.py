# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_datacarrier`, rewritten on tf2's own harness: btcd.

`mempool_datacarrier_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/mempool_datacarrier_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_datacarrier_test import (
    bare_multisig_is_permitted_by_default,
    datacarrier_disabled_refuses_any_null_data_output,
    datacarriersize_bounds_the_payload,
    default_settings_allow_a_large_op_return,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_default_settings_allow_a_large_op_return(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    default_settings_allow_a_large_op_return(btcd_cluster, skip_counts)


def test_datacarrier_disabled_refuses_any_null_data_output(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    datacarrier_disabled_refuses_any_null_data_output(btcd_cluster, skip_counts)


def test_datacarriersize_bounds_the_payload(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    datacarriersize_bounds_the_payload(btcd_cluster, skip_counts)


def test_bare_multisig_is_permitted_by_default(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    bare_multisig_is_permitted_by_default(btcd_cluster, skip_counts)
