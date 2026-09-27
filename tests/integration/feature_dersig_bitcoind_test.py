# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_dersig`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/feature_dersig.py`:
`feature_dersig_test.py` beside this module holds each body, run here
against bitcoind, which declares every capability they ask for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_dersig_activates_one_block_before_the_configured_height(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    dersig_activates_one_block_before_the_configured_height(
        bitcoind_cluster, skip_counts
    )


def test_a_block_below_the_minimum_version_is_refused(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_block_below_the_minimum_version_is_refused(bitcoind_cluster, skip_counts)


def test_a_block_below_the_minimum_version_is_logged(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_block_below_the_minimum_version_is_logged(bitcoind_cluster, skip_counts)


def test_a_non_der_signature_is_refused_once_active(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_non_der_signature_is_refused_once_active(bitcoind_cluster, skip_counts)
