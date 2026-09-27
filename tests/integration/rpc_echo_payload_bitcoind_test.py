# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_echo_payload`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_echo_payload.py`:
`rpc_echo_payload_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_echo_payload_test import (
    a_payload_is_answered_or_refused_never_left_to_time_out,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_a_payload_is_answered_or_refused_never_left_to_time_out(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_payload_is_answered_or_refused_never_left_to_time_out(
        bitcoind_cluster, skip_counts
    )
