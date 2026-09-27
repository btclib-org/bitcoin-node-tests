# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_includeconf`, rewritten on this repository's own harness.

Read from Core's `test/functional/feature_includeconf.py`:
`feature_includeconf_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_includeconf_test import (
    a_missing_included_file_is_refused,
    a_nested_includeconf_is_ignored_with_a_warning,
    includeconf_files_are_read_in_order,
    includeconf_on_the_command_line_is_refused,
    noincludeconf_0_on_the_command_line_is_refused,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_includeconf_files_are_read_in_order(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the order the body module names, over bitcoind."""
    includeconf_files_are_read_in_order(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_noincludeconf_0_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: `-noincludeconf=0` refused, over bitcoind."""
    noincludeconf_0_on_the_command_line_is_refused(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_includeconf_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: `-includeconf=<file>` refused, over bitcoind."""
    includeconf_on_the_command_line_is_refused(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_a_nested_includeconf_is_ignored_with_a_warning(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: the nested `includeconf` warned about, over bitcoind."""
    a_nested_includeconf_is_ignored_with_a_warning(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )


def test_a_missing_included_file_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
) -> None:
    """The oracle: the missing included file refused, over bitcoind."""
    a_missing_included_file_is_refused(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path
    )
