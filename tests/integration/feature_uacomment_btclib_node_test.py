# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_uacomment`, rewritten on this harness: btclib-node.

The same claim `feature_uacomment_bitcoind_test.py` makes, against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
`-uacomment` is not one of `cli.py`'s own registered flags
(`btclib_node.py`'s own docstring has the measurement), so
`Capability.UA_COMMENT` is never declared here and this counts a skip
rather than a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/feature_uacomment_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_uacomment_appends_to_the_subversion_string(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.UA_COMMENT` is not declared, so this counts a skip.

    Checked before a node is ever spawned, the same way
    `feature_blocksdir_btclib_node_test.py`'s own `BLK_FILES` case is:
    the capability is the class's own, unconditional on the instance.
    `btclib_node_python` is asked for anyway -- unused otherwise -- so
    that this still skips itself without `TF2_INTEGRATION`, the way
    every other test under `tests/integration/` does.
    """
    del btclib_node_python
    require(Capability.UA_COMMENT, BtclibNodeAdapter.capabilities, skip_counts)
