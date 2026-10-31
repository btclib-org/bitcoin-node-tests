# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getaddr_caching`, rewritten on tf2's own harness: btcd.

`p2p_getaddr_caching_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/p2p_getaddr_caching_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.p2p_getaddr_caching_test import (
    getaddr_answers_are_cached_per_bind,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_getaddr_answers_are_cached_per_bind(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: one cached `getaddr` answer per bind, over btcd."""
    getaddr_answers_are_cached_per_bind(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
