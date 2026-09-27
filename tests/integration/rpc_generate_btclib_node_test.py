# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Core's `rpc_generate`, rewritten on tf2's own harness: btclib-node.

`rpc_generate_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). `Capability.GENERATE` is not declared
(`btclib_node.py`'s own docstring is why), so each is a counted skip
ahead of `Capability.MINE`.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_generate_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.rpc_generate_test import (
    generate_is_a_hidden_command_naming_the_cli_option,
    generateblock_mines_what_it_is_handed,
    generatetoaddress_refuses_another_chain_s_address,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_generatetoaddress_refuses_another_chain_s_address(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    generatetoaddress_refuses_another_chain_s_address(btclib_node_cluster, skip_counts)


def test_generate_is_a_hidden_command_naming_the_cli_option(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    generate_is_a_hidden_command_naming_the_cli_option(btclib_node_cluster, skip_counts)


def test_generateblock_mines_what_it_is_handed(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    generateblock_mines_what_it_is_handed(btclib_node_cluster, skip_counts)
