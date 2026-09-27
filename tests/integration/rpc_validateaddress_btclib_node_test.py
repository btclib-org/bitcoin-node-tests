# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_validateaddress`, rewritten on this harness: btclib-node.

The same requests `rpc_validateaddress_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`Capability.VALIDATE_ADDRESS` is not declared (`btclib_node.py`'s own
docstring is why: `validateaddress` names no callback in its dispatch
table, on either build), so each subject is a counted skip on that
capability alone, before any node is spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_validateaddress_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_invalid_addresses_answer_their_error(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.VALIDATE_ADDRESS` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.VALIDATE_ADDRESS, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")


def test_valid_addresses_answer_their_script_pub_key(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.VALIDATE_ADDRESS` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.VALIDATE_ADDRESS, BtclibNodeAdapter.capabilities, skip_counts)
    pytest.fail("not ported for this node")
