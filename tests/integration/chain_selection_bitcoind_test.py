# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`NodeAdapter`'s own `chain`, against a real node: bitcoind.

`chain_selection_test.py` beside this module is the body, run here
against bitcoind, the oracle, once for each chain
`BitcoindAdapter.chains` names
([ISS 63](https://github.com/btclib-org/btclib-functional-tests/issues/63)).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.bitcoind import BitcoindAdapter
from tests.integration.chain_selection_test import (
    node_starts_on_the_chain_it_is_given,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("chain", sorted(BitcoindAdapter.chains))
def test_node_starts_on_the_chain_it_is_given(
    make_adapter: AdapterFactory, bitcoind_path: str, tmp_path: Path, chain: str
) -> None:
    """The oracle: the chain the adapter was built with, over bitcoind."""
    node_starts_on_the_chain_it_is_given(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, chain
    )
