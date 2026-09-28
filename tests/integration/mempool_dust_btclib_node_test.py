# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_dust`, rewritten on this harness: btclib-node.

`mempool_dust_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.PERMIT_BARE_MULTISIG` is not
declared: measured against `cli.py`'s registered options,
`_build_parser` on the released build and `_OPTIONS` on `main`,
`-permitbaremultisig` is not one of its registered flags -- a counted
skip on that capability alone, before the node is restarted with it.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/mempool_dust_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_dust_test import (
    a_value_clearly_above_the_dust_threshold_is_allowed,
    a_value_clearly_below_the_dust_threshold_is_refused,
    dustrelayfee_zero_waives_the_dust_check,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_value_clearly_below_the_dust_threshold_is_refused(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_value_clearly_below_the_dust_threshold_is_refused(
        btclib_node_cluster, skip_counts
    )


def test_a_value_clearly_above_the_dust_threshold_is_allowed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    a_value_clearly_above_the_dust_threshold_is_allowed(
        btclib_node_cluster, skip_counts
    )


def test_dustrelayfee_zero_waives_the_dust_check(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    dustrelayfee_zero_waives_the_dust_check(btclib_node_cluster, skip_counts)
