# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_eviction`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/p2p_eviction.py`: `p2p_eviction_test.py`
beside this module holds the body, run here against bitcoind, whose
`-help` is read with `-nosettings` for the reason `bitcoind.py`'s own
`_has_wallet` gives.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_eviction_test import (
    the_evicted_inbound_peer_is_never_a_protected_one,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_the_evicted_inbound_peer_is_never_a_protected_one(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    bitcoind_path: str,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    the_evicted_inbound_peer_is_never_a_protected_one(
        bitcoind_cluster, (bitcoind_path, "-help", "-nosettings"), skip_counts
    )
