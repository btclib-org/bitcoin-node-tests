# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptorinfo`, rewritten on this harness: btclib-node.

`rpc_getdescriptorinfo_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DESCRIPTOR_INFO` is not declared
(`btclib_node.py`'s own docstring is why: `getdescriptorinfo` names no
callback in its dispatch table, on either build), so each test is a
counted skip on that capability.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_getdescriptorinfo_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_getdescriptorinfo_test import (
    descriptors_answer_their_info,
    malformed_requests_are_refused,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_malformed_requests_are_refused(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the refusals the body module names, over btclib-node."""
    malformed_requests_are_refused(btclib_node_adapter, skip_counts)


def test_descriptors_answer_their_info(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: the answers the body module names, over btclib-node."""
    descriptors_answer_their_info(btclib_node_adapter, skip_counts)
