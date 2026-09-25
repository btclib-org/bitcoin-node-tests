# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `mempool_datacarrier`, rewritten on this harness: btclib-node.

The same requests `mempool_datacarrier_bitcoind_test.py` makes, against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.DATACARRIER` is not declared:
measured against `cli.py`'s registered options, `_build_parser` on the
released build and `_OPTIONS` on `main`, neither `-datacarrier` nor
`-datacarriersize` is one of its registered flags -- a counted skip on
that capability alone, before any node is ever spawned.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest \\
        tests/integration/mempool_datacarrier_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_default_settings_allow_a_large_op_return(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.DATACARRIER` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.DATACARRIER, BtclibNodeAdapter.capabilities, skip_counts)


def test_datacarrier_disabled_refuses_any_null_data_output(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.DATACARRIER` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.DATACARRIER, BtclibNodeAdapter.capabilities, skip_counts)


def test_datacarriersize_bounds_the_payload(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.DATACARRIER` is not declared, so this skips."""
    del btclib_node_python
    require(Capability.DATACARRIER, BtclibNodeAdapter.capabilities, skip_counts)


def test_bare_multisig_is_permitted_by_default(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.PERMIT_BARE_MULTISIG` is not declared, so this skips."""
    del btclib_node_python
    require(
        Capability.PERMIT_BARE_MULTISIG, BtclibNodeAdapter.capabilities, skip_counts
    )
