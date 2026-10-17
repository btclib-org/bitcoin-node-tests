# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `p2p_headers_sync_with_minchainwork`, rewritten here: btcd.

`p2p_headers_sync_with_minchainwork_test.py` beside this module is the
body, run here against btcd, a target rather than the oracle (rule 3 of
issue btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration \
        -k p2p_headers_sync_with_minchainwork_btcd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_headers_sync_with_minchainwork_test import (
    TEST_TIMEOUT,
    low_work_headers_are_ignored_until_the_chain_has_the_work,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btcd import BtcdAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


@pytest.mark.scaled_timeout(TEST_TIMEOUT)
def test_low_work_headers_are_ignored_until_the_chain_has_the_work(
    btcd_cluster: Callable[[int], list[BtcdAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    low_work_headers_are_ignored_until_the_chain_has_the_work(btcd_cluster, skip_counts)
