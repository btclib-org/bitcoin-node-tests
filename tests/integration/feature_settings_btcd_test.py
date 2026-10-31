# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_settings`, rewritten on tf2's own harness: btcd.

`feature_settings_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_settings_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.feature_settings_test import (
    the_settings_file_is_written_read_and_checked,
    the_wallet_setting_takes_only_strings,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_the_settings_file_is_written_read_and_checked(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the settings file the body module names, over btcd."""
    the_settings_file_is_written_read_and_checked(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_the_wallet_setting_takes_only_strings(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: a `wallet` value not a string refused, over btcd."""
    the_wallet_setting_takes_only_strings(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
