# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_generate`, rewritten on tf2's own harness: bitcoind.

Read from Core's `test/functional/rpc_generate.py`: `rpc_generate_test.py`
beside this module is the body, run here against bitcoind, which declares
every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
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

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_generatetoaddress_refuses_another_chain_s_address(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    generatetoaddress_refuses_another_chain_s_address(bitcoind_cluster, skip_counts)


def test_generate_is_a_hidden_command_naming_the_cli_option(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    generate_is_a_hidden_command_naming_the_cli_option(bitcoind_cluster, skip_counts)


def test_generateblock_mines_what_it_is_handed(
    bitcoind_cluster: Callable[[int], list[BitcoindAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    generateblock_mines_what_it_is_handed(bitcoind_cluster, skip_counts)
