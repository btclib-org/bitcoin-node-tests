# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `wallet_blank`, on tf2's own harness: btclib-node.

`wallet_blank_test.py` beside this module holds each body, run
here against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.NODE_WALLET` is not declared:
btclib-node keeps no wallet (`btclib_node.py`'s own docstring), and a
wallet kept beside it is
[ISS 199](https://github.com/btclib-org/bitcoin-node-tests/issues/199)'s
to reach -- a counted skip on that capability, asked for first.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \
        tests/integration/wallet_blank_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_blank_test import (
    encryptwallet_keeps_the_blank_flag_and_the_descriptors,
    importdescriptors_keeps_the_blank_flag,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_importdescriptors_keeps_the_blank_flag(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    importdescriptors_keeps_the_blank_flag(btclib_node_cluster, skip_counts)


def test_encryptwallet_keeps_the_blank_flag_and_the_descriptors(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    encryptwallet_keeps_the_blank_flag_and_the_descriptors(
        btclib_node_cluster, skip_counts
    )
