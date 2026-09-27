# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_blank`, on this repository's own harness: bitcoind.

Read from Core's `test/functional/wallet_blank.py`:
`wallet_blank_test.py` beside this module holds each body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_importdescriptors_keeps_the_blank_flag(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    importdescriptors_keeps_the_blank_flag(bitcoind_cluster, skip_counts)


def test_encryptwallet_keeps_the_blank_flag_and_the_descriptors(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    encryptwallet_keeps_the_blank_flag_and_the_descriptors(
        bitcoind_cluster, skip_counts
    )
