# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_whitelist`, rewritten on tf2's own harness: btcd.

`rpc_whitelist_test.py` beside this module is the body, run here against
btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/rpc_whitelist_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.rpc_whitelist_test import (
    a_rejected_method_is_logged_as_named,
    rpcwhitelist_restricts_a_users_own_rpc_surface,
    rpcwhitelistdefault_governs_an_unlisted_user,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_rpcwhitelist_restricts_a_users_own_rpc_surface(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a whitelisted user reaches only its own methods."""
    rpcwhitelist_restricts_a_users_own_rpc_surface(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_rejected_method_is_logged_as_named(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_rejected_method_is_logged_as_named(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_rpcwhitelistdefault_governs_an_unlisted_user(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `rpcwhitelistdefault=1` refuses an unlisted user."""
    rpcwhitelistdefault_governs_an_unlisted_user(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
