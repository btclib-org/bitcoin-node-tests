# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptorinfo`, rewritten on tf2's own harness: btcd.

`rpc_getdescriptorinfo_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_getdescriptorinfo_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_getdescriptorinfo_test import (
    descriptors_answer_their_info,
    malformed_requests_are_refused,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_malformed_requests_are_refused(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the refusals the body module names, over btcd."""
    malformed_requests_are_refused(btcd_adapter, skip_counts)


def test_descriptors_answer_their_info(
    btcd_adapter: BtcdAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the answers the body module names, over btcd."""
    descriptors_answer_their_info(btcd_adapter, skip_counts)
