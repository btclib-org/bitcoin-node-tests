# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, against a real node: btcd.

`chain_selection_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/chain_selection_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.chain_selection_test import (
    node_starts_on_the_chain_it_is_given,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("chain", sorted(BtcdAdapter.chains))
def test_node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory, btcd_path: str, tmp_path: Path, chain: str
) -> None:
    """The target: the chain the adapter was built with, over btcd."""
    node_starts_on_the_chain_it_is_given(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, chain
    )
