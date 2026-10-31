# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_users`, rewritten on this repository's harness: bitcoind.

`rpc_users_test.py` beside this module is the body, run here against
bitcoind, the oracle, which declares `Capability.RPC_AUTH_CONFIG` and
`Capability.RPC_AUTH_NEGATION`.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.bitcoind import BitcoindAdapter
from tests.integration.rpc_users_test import (
    BLANK_RPCAUTH_POSITIONS,
    COOKIE_PERMISSIONS,
    MALFORMED_RPCAUTH,
    blank_rpcauth_refuses_regardless_of_position,
    cookie_write_failure_aborts_the_node,
    malformed_rpcauth_refuses_to_start,
    norpcauth_disables_previous_rpcauth,
    norpccookiefile_writes_no_cookie_and_rpcauth_still_authenticates,
    rpcauth_on_command_line_authenticates,
    rpcauth_via_config_authenticates_and_refuses,
    rpccookieperms_sets_posix_permission_bits,
    rpcuser_rpcpassword_authenticates_without_a_cookie,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_rpcauth_via_config_authenticates_and_refuses(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `rpcauth` from `bitcoin.conf` authenticates and refuses."""
    rpcauth_via_config_authenticates_and_refuses(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_rpcauth_on_command_line_authenticates(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-rpcauth` on the command line authenticates."""
    rpcauth_on_command_line_authenticates(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


@pytest.mark.parametrize("rpcauth", MALFORMED_RPCAUTH)
def test_malformed_rpcauth_refuses_to_start(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    rpcauth: str,
) -> None:
    """The oracle: a malformed `-rpcauth` is fatal."""
    malformed_rpcauth_refuses_to_start(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts, rpcauth
    )


@pytest.mark.parametrize("extra_args", BLANK_RPCAUTH_POSITIONS)
def test_blank_rpcauth_refuses_regardless_of_position(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    extra_args: tuple[str, ...],
) -> None:
    """The oracle: a blank `-rpcauth=` is fatal wherever it sits."""
    blank_rpcauth_refuses_regardless_of_position(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts, extra_args
    )


def test_norpcauth_disables_previous_rpcauth(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-norpcauth` disables earlier `-rpcauth` values."""
    norpcauth_disables_previous_rpcauth(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_rpcuser_rpcpassword_authenticates_without_a_cookie(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-rpcuser`/`-rpcpassword` authenticates with no cookie."""
    rpcuser_rpcpassword_authenticates_without_a_cookie(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_norpccookiefile_writes_no_cookie_and_rpcauth_still_authenticates(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-norpccookiefile` writes no cookie."""
    norpccookiefile_writes_no_cookie_and_rpcauth_still_authenticates(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


@pytest.mark.parametrize("perm, expected_mode", COOKIE_PERMISSIONS)
def test_rpccookieperms_sets_posix_permission_bits(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
    perm: str | None,
    expected_mode: int,
) -> None:
    """The oracle: `-rpccookieperms` sets the cookie's mode."""
    rpccookieperms_sets_posix_permission_bits(
        make_adapter,
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        skip_counts,
        perm,
        expected_mode,
    )


def test_cookie_write_failure_aborts_the_node(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a cookie that cannot be written is fatal."""
    cookie_write_failure_aborts_the_node(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
