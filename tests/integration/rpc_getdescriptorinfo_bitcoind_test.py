# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptorinfo`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getdescriptorinfo.py`:
`rpc_getdescriptorinfo_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_getdescriptorinfo_test import (
    descriptors_answer_their_info,
    malformed_requests_are_refused,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_malformed_requests_are_refused(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the refusals the body module names, over bitcoind."""
    malformed_requests_are_refused(bitcoind_adapter, skip_counts)


def test_descriptors_answer_their_info(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the answers the body module names, over bitcoind."""
    descriptors_answer_their_info(bitcoind_adapter, skip_counts)
