# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_whitelist`, rewritten on this repository's harness: bitcoind.

`rpc_whitelist_test.py` beside this module is the body, run here against
bitcoind, the oracle, which declares `Capability.RPC_AUTH_CONFIG`.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.rpc_whitelist_test import (
    a_rejected_method_is_logged_as_named,
    rpcwhitelist_restricts_a_users_own_rpc_surface,
    rpcwhitelistdefault_governs_an_unlisted_user,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_rpcwhitelist_restricts_a_users_own_rpc_surface(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a whitelisted user reaches only its own methods."""
    rpcwhitelist_restricts_a_users_own_rpc_surface(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_a_rejected_method_is_logged_as_named(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_rejected_method_is_logged_as_named(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_rpcwhitelistdefault_governs_an_unlisted_user(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `rpcwhitelistdefault=1` refuses an unlisted user."""
    rpcwhitelistdefault_governs_an_unlisted_user(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
