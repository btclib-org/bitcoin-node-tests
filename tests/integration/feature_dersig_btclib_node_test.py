# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `feature_dersig`, rewritten on this harness: btclib-node.

`feature_dersig_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.TEST_ACTIVATION_HEIGHT` is not
declared: measured against `cli.py`'s registered options, `_build_parser`
on the released build and `_OPTIONS` on `main` (`btclib_node.py`'s own
docstring has the same measurement for `-uacomment`),
`-testactivationheight` is not one of its registered flags -- a counted
skip on that capability alone, before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/feature_dersig_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_dersig_activates_one_block_before_the_configured_height(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    dersig_activates_one_block_before_the_configured_height(
        btclib_node_cluster, skip_counts
    )


def test_a_block_below_the_minimum_version_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_block_below_the_minimum_version_is_refused(btclib_node_cluster, skip_counts)


def test_a_block_below_the_minimum_version_is_logged(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_block_below_the_minimum_version_is_logged(btclib_node_cluster, skip_counts)


def test_a_non_der_signature_is_refused_once_active(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_non_der_signature_is_refused_once_active(btclib_node_cluster, skip_counts)
