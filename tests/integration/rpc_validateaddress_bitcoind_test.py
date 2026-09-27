# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_validateaddress`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_validateaddress.py`:
`rpc_validateaddress_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
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
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the refusals the body module names, over bitcoind."""
    invalid_addresses_answer_their_error(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_valid_addresses_answer_their_script_pub_key(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the scripts the body module names, over bitcoind."""
    valid_addresses_answer_their_script_pub_key(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
