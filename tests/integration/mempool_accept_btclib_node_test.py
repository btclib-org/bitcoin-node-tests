# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_accept`, rewritten on tf2's own harness: btclib-node.

`mempool_accept_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.PERMIT_BARE_MULTISIG` is not
declared: measured against `cli.py`'s registered options,
`_build_parser` on the released build and `_OPTIONS` on `main`,
`-permitbaremultisig` is not one of its registered flags
([ISS btclib-node#1497](https://github.com/btclib-org/btclib-node/issues/1497))
-- a counted skip on that capability alone, on every build, before
`Capability.MINE` is asked for.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/mempool_accept_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.mempool_accept_test import (
    mempool_acceptance_of_raw_transactions,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_mempool_acceptance_of_raw_transactions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    mempool_acceptance_of_raw_transactions(btclib_node_cluster, skip_counts)
