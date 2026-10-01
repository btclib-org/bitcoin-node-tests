# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_assumevalid`, rewritten on tf2's own harness: btclib-node.

`feature_assumevalid_test.py` beside this module is the body, run here
against the target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220). The test is a counted skip on
`Capability.ASSUME_VALID`, which `btclib_node.py`'s own docstring has no
build declaring.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_assumevalid_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.feature_assumevalid_test import (
    TEST_TIMEOUT,
    script_verification_depends_on_assumevalid_and_its_conditions,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


@pytest.mark.scaled_timeout(TEST_TIMEOUT)
def test_script_verification_depends_on_assumevalid_and_its_conditions(
    btclib_node_cluster: Callable[[int], list[BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btclib-node."""
    script_verification_depends_on_assumevalid_and_its_conditions(
        btclib_node_cluster, skip_counts
    )
