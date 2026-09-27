# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`scaled`, `set_factor` and `rpc_client_timeout`, apart from their callers."""

from __future__ import annotations

import pytest

from bitcoin_node_tests.timeout_factor import (
    rpc_client_timeout,
    scaled,
    set_factor,
)


def test_scaled_defaults_to_the_value_given_unchanged() -> None:
    """No `set_factor` call yet in this process: `1.0` is the multiplier."""
    assert scaled(30.0) == 30.0


def test_set_factor_changes_what_scaled_answers() -> None:
    """`set_factor` is what `scaled` reads, and it is process-global."""
    set_factor(2.5)
    try:
        assert scaled(4.0) == 10.0
    finally:
        set_factor(1.0)


@pytest.mark.parametrize(
    "factor, expected",
    [(1.0, 30), (3.0, 90), (0.5, 15), (1.01, 30), (0.03, 0)],
)
def test_rpc_client_timeout_is_core_s_rpc_timeout_halved(
    factor: float, expected: int
) -> None:
    """`int(60 * factor) // 2`, truncated twice exactly as Core truncates it."""
    set_factor(factor)
    try:
        assert rpc_client_timeout() == expected
    finally:
        set_factor(1.0)
