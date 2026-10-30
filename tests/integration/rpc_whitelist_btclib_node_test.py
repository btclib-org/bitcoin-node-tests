# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_whitelist`, rewritten on this harness: btclib-node.

`rpc_whitelist_test.py` beside this module is the body, run here against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
A build with
[ISS btclib-node#1070](https://github.com/btclib-org/btclib-node/issues/1070)
runs the same assertions the oracle does; one without it counts a skip
instead of a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/rpc_whitelist_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
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
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a whitelisted user reaches only its own methods."""
    rpcwhitelist_restricts_a_users_own_rpc_surface(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_a_rejected_method_is_logged_as_named(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a whitelisted user reaches only its own methods."""
    a_rejected_method_is_logged_as_named(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_rpcwhitelistdefault_governs_an_unlisted_user(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `rpcwhitelistdefault=1` refuses an unlisted user."""
    rpcwhitelistdefault_governs_an_unlisted_user(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
