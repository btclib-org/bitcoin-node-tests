# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_i2p_ports`, rewritten on this repository's harness: bitcoind.

Read from Core's `test/functional/p2p_i2p_ports.py`:
`p2p_i2p_ports_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_i2p_ports_test import i2p_is_dialled_on_port_zero_alone

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_i2p_is_dialled_on_port_zero_alone(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    i2p_is_dialled_on_port_zero_alone(bitcoind_cluster, skip_counts)
