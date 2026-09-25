# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--v2transport`, restated through the adapter: btclib-node.

The same subject `v2transport_option_bitcoind_test.py` measures, against
the target rather than the oracle (rule 3 of issue btclib-org/btclib#2220):
`Capability.V2TRANSPORT` is never declared here -- `btclib_node.py`'s own
module docstring has the measurement, `addnode`'s own `v2transport`
parameter read and discarded with no BIP324 codec behind it -- so this
counts a skip rather than a silent pass.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/v2transport_option_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_v2transport_is_not_declared(
    btclib_node_python: str, skip_counts: SkipCounts
) -> None:
    """`Capability.V2TRANSPORT` is not declared, so this counts a skip.

    Checked before a node is ever spawned, the same way
    `feature_uacomment_btclib_node_test.py`'s own case is: the capability
    is the class's own, unconditional on the instance. `btclib_node_python`
    is asked for anyway -- unused otherwise -- so that this still skips
    itself without `TF2_INTEGRATION`, the way every other test under
    `tests/integration/` does.
    """
    del btclib_node_python
    require(Capability.V2TRANSPORT, BtclibNodeAdapter.capabilities, skip_counts)
