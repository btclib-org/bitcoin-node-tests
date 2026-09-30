# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_settings`, rewritten on this repository's own harness.

Read from Core's `test/functional/feature_settings.py`:
`feature_settings_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_settings_test import (
    the_settings_file_is_written_read_and_checked,
    the_wallet_setting_takes_only_strings,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_the_settings_file_is_written_read_and_checked(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the settings file the body module names, over bitcoind."""
    the_settings_file_is_written_read_and_checked(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_the_wallet_setting_takes_only_strings(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: a `wallet` value not a string refused, over bitcoind."""
    the_wallet_setting_takes_only_strings(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
