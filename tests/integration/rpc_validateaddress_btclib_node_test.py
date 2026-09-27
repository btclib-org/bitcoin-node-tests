# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_validateaddress`, rewritten on this harness: btclib-node.

`rpc_validateaddress_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.VALIDATE_ADDRESS` is not declared
(`btclib_node.py`'s own docstring is why: `validateaddress` names no
callback in its dispatch table, on either build), so each test is a
counted skip on that capability, asked of the node before it starts.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_validateaddress_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.rpc_validateaddress_test import (
    invalid_addresses_answer_their_error,
    valid_addresses_answer_their_script_pub_key,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_invalid_addresses_answer_their_error(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the refusals the body module names, over btclib-node."""
    invalid_addresses_answer_their_error(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_valid_addresses_answer_their_script_pub_key(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the scripts the body module names, over btclib-node."""
    valid_addresses_answer_their_script_pub_key(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
