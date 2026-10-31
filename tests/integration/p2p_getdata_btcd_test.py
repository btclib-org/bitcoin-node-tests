# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getdata`, rewritten on tf2's own harness: btcd.

`p2p_getdata_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_getdata_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_getdata_test import (
    invalid_getdata_does_not_stop_a_later_valid_one,
)

if TYPE_CHECKING:
    from btclib_functional_tests.btcd import BtcdAdapter

pytestmark = pytest.mark.integration


def test_invalid_getdata_does_not_stop_a_later_valid_one(
    btcd_adapter: BtcdAdapter,
) -> None:
    """The target: the invalid item first, the valid one still served."""
    invalid_getdata_does_not_stop_a_later_valid_one(btcd_adapter)
