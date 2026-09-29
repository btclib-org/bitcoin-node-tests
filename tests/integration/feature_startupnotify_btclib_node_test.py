# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_startupnotify`, rewritten on this harness: btclib-node.

`feature_startupnotify_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test is a counted skip on
`Capability.STARTUP_NOTIFY`, which `btclib_node.py`'s own docstring has
no build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_startupnotify_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from tests.integration.feature_startupnotify_test import (
    the_startup_command_runs_once,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_the_startup_command_runs_once(
    make_adapter: AdapterFactory,
    btclib_node_python: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the startup command run once, over btclib-node."""
    the_startup_command_runs_once(
        make_adapter, BtclibNodeAdapter, btclib_node_python, tmp_path, skip_counts
    )
