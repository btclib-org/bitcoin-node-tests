# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getdata`, rewritten on this repository's own harness: bitcoind.

`p2p_getdata_test.py` beside this module is the body, run here against
bitcoind, the oracle.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_getdata_test import (
    invalid_getdata_does_not_stop_a_later_valid_one,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter

pytestmark = pytest.mark.integration


def test_invalid_getdata_does_not_stop_a_later_valid_one(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the invalid item first, the valid one still served."""
    invalid_getdata_does_not_stop_a_later_valid_one(bitcoind_adapter)
