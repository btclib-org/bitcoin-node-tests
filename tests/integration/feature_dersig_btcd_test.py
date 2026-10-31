# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dersig`, rewritten on tf2's own harness: btcd.

`feature_dersig_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_dersig_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_dersig_test import (
    a_block_below_the_minimum_version_is_logged,
    a_block_below_the_minimum_version_is_refused,
    a_non_der_signature_is_refused_once_active,
    dersig_activates_one_block_before_the_configured_height,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from btclib_functional_tests.btcd import BtcdAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_dersig_activates_one_block_before_the_configured_height(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    dersig_activates_one_block_before_the_configured_height(btcd_cluster, skip_counts)


def test_a_block_below_the_minimum_version_is_refused(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_block_below_the_minimum_version_is_refused(btcd_cluster, skip_counts)


def test_a_block_below_the_minimum_version_is_logged(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_block_below_the_minimum_version_is_logged(btcd_cluster, skip_counts)


def test_a_non_der_signature_is_refused_once_active(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_non_der_signature_is_refused_once_active(btcd_cluster, skip_counts)
