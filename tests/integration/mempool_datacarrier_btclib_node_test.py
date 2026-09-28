# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_datacarrier`, rewritten on this harness: btclib-node.

`mempool_datacarrier_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). Neither `Capability.DATACARRIER` nor
`Capability.PERMIT_BARE_MULTISIG` is declared: measured against
`cli.py`'s registered options, `_build_parser` on the released build
and `_OPTIONS` on `main`, none of `-datacarrier`, `-datacarriersize`
and `-permitbaremultisig` is one of its registered flags -- each body a
counted skip on whichever of the two it asks for.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/mempool_datacarrier_btclib_node_test.py
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

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_default_settings_allow_a_large_op_return(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    default_settings_allow_a_large_op_return(btclib_node_cluster, skip_counts)


def test_datacarrier_disabled_refuses_any_null_data_output(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    datacarrier_disabled_refuses_any_null_data_output(btclib_node_cluster, skip_counts)


def test_datacarriersize_bounds_the_payload(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    datacarriersize_bounds_the_payload(btclib_node_cluster, skip_counts)


def test_bare_multisig_is_permitted_by_default(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    bare_multisig_is_permitted_by_default(btclib_node_cluster, skip_counts)
