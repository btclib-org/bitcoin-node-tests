# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`timeout_factor`'s own functions, apart from their callers."""

from __future__ import annotations

import pytest

from bitcoin_node_tests.timeout_factor import (
    factor_from_option,
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


@pytest.mark.parametrize(
    "value, expected",
    [("0", 999.0), ("0.0", 999.0), ("-0", 999.0), ("2.5", 2.5), ("-1", -1.0)],
)
def test_factor_from_option_reads_0_as_core_does(value: str, expected: float) -> None:
    """0 is Core's 999; any other number, a negative one too, is kept."""
    assert factor_from_option(value) == expected


def test_factor_from_option_refuses_what_is_not_a_number() -> None:
    """The option's own text is parsed as `float` parses it."""
    with pytest.raises(ValueError, match="could not convert"):
        factor_from_option("fast")


def test_factor_0_leaves_the_rpc_client_a_timeout_it_accepts() -> None:
    """`--timeout-factor 0` bounds an RPC call at Core's own 29970 s."""
    set_factor(factor_from_option("0"))
    try:
        assert rpc_client_timeout() == 29970
    finally:
        set_factor(1.0)
