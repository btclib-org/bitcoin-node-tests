# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `wallet_createwalletdescriptor`, on this harness: bitcoind.

Read from Core's `test/functional/wallet_createwalletdescriptor.py`:
`wallet_createwalletdescriptor_test.py` beside this module holds the body,
run here against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.wallet_createwalletdescriptor_test import (
    createwalletdescriptor_derives_from_a_key_the_wallet_holds,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_createwalletdescriptor_derives_from_a_key_the_wallet_holds(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    createwalletdescriptor_derives_from_a_key_the_wallet_holds(
        bitcoind_cluster, skip_counts
    )
