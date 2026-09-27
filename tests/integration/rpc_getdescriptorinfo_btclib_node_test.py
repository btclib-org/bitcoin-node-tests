# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_getdescriptorinfo`, rewritten on this harness: btclib-node.

The same requests `rpc_getdescriptorinfo_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.DESCRIPTOR_INFO` is not declared (`btclib_node.py`'s own
docstring is why: `getdescriptorinfo` names no callback in its dispatch
table, on either build), so each subject is a counted skip on that
capability alone, before any node is spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_getdescriptorinfo_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_malformed_requests_are_refused(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.DESCRIPTOR_INFO` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.DESCRIPTOR_INFO, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_descriptors_answer_their_info(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.DESCRIPTOR_INFO` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.DESCRIPTOR_INFO, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
