# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`scaled` and `set_factor`, in isolation from every caller of either."""

from __future__ import annotations

from bitcoin_node_tests.timeout_factor import scaled, set_factor


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
