# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_validateaddress`, rewritten on tf2's own harness: btcd.

`rpc_validateaddress_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_validateaddress_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btcd import BtcdAdapter
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
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the refusals the body module names, over btcd."""
    invalid_addresses_answer_their_error(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_valid_addresses_answer_their_script_pub_key(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the scripts the body module names, over btcd."""
    valid_addresses_answer_their_script_pub_key(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
