# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_includeconf`, rewritten on tf2's own harness: btcd.

`feature_includeconf_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_includeconf_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.feature_includeconf_test import (
    a_missing_included_file_is_refused,
    a_nested_includeconf_is_ignored_with_a_warning,
    includeconf_files_are_read_in_order,
    includeconf_on_the_command_line_is_refused,
    noincludeconf_0_on_the_command_line_is_refused,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_includeconf_files_are_read_in_order(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the order the body module names, over btcd."""
    includeconf_files_are_read_in_order(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_noincludeconf_0_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-noincludeconf=0` refused, over btcd."""
    noincludeconf_0_on_the_command_line_is_refused(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_includeconf_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: `-includeconf=<file>` refused, over btcd."""
    includeconf_on_the_command_line_is_refused(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_nested_includeconf_is_ignored_with_a_warning(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the nested `includeconf` warned about, over btcd."""
    a_nested_includeconf_is_ignored_with_a_warning(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_missing_included_file_is_refused(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the missing included file refused, over btcd."""
    a_missing_included_file_is_refused(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
