# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_dust`, rewritten on this harness: btclib-node.

`mempool_dust_test.py` beside this module holds each body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.PERMIT_BARE_MULTISIG` is declared on a
build whose `cli.py` registers `-permitbaremultisig`: `v2026.10.4`
(`f1732715`) and `main` (`6777a6a8`). There the refusal and allowance
bodies run. On `v2026.10.4` a one-satoshi output paying a fee is allowed,
where Core refuses it as `dust`
([ISS btclib-node#1594](https://github.com/btclib-org/btclib-node/issues/1594)).
`Capability.DUST_RELAY_FEE` is not declared, so the `-dustrelayfee=0` body
is a counted skip. On `v2026.9.24` (`422d2640`) every body is a counted
skip on `PERMIT_BARE_MULTISIG`.

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
