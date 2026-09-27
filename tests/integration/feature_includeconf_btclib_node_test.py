# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_includeconf`, rewritten on this harness: btclib-node.

`feature_includeconf_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The order is a counted skip on
`Capability.UA_COMMENT`, which `btclib_node.py`'s own docstring has no
build declaring; every other test asks for no capability and runs.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_includeconf_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
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
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the order the body module names, over btclib-node."""
    includeconf_files_are_read_in_order(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )


def test_noincludeconf_0_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: `-noincludeconf=0` refused, over btclib-node."""
    noincludeconf_0_on_the_command_line_is_refused(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_includeconf_on_the_command_line_is_refused(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: `-includeconf=<file>` refused, over btclib-node."""
    includeconf_on_the_command_line_is_refused(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_a_nested_includeconf_is_ignored_with_a_warning(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: the nested `includeconf` warned about, over btclib-node."""
    a_nested_includeconf_is_ignored_with_a_warning(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )


def test_a_missing_included_file_is_refused(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
) -> None:
    """The target: the missing included file refused, over btclib-node."""
    a_missing_included_file_is_refused(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path
    )
