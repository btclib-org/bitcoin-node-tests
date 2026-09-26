# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_sigoplimit`, rewritten on this harness: btclib-node.

The same request `mempool_sigoplimit_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.BYTES_PER_SIGOP` is not declared:
measured against `cli.py`'s registered options, `_build_parser` on the
released build and `_OPTIONS` on `main`, `-bytespersigop` is not one of
its registered flags -- a counted skip on that capability alone, before
any node is ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_sigoplimit_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_sigop_heavy_transaction_is_billed_by_its_equivalent_vsize(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.BYTES_PER_SIGOP` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.BYTES_PER_SIGOP, BtclibNodeAdapter.capabilities, skip_counts)
    require(Capability.MINE, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
