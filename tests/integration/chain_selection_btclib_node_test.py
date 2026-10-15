# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, against a real node: btclib-node.

`chain_selection_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220), once for each chain `BtclibNodeAdapter.chains`
names
([ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63)).

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/chain_selection_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.chain_selection_test import (
    node_starts_on_the_chain_it_is_given,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("chain", sorted(BtclibNodeAdapter.chains))
def test_node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory, btclib_node_python: str, tmp_path: Path, chain: str
) -> None:
    """The target: the chain the adapter was built with, over btclib-node."""
    node_starts_on_the_chain_it_is_given(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, chain
    )
