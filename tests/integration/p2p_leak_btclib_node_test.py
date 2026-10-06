# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_leak`, rewritten on tf2's own harness: btclib-node.

`p2p_leak_test.py` beside this module is the body, run here against the
target rather than the oracle (rule 3 of issue btclib-org/btclib#2220).
`btclib-node`'s own `p2p.callbacks.version` refuses a peer below a floor
of its own: PyPI's `2026.9.24` on `version_msg.version < PROTOCOL_VERSION`
(`70016`), `main` on Core's own `MIN_PEER_PROTO_VERSION` (`31800`,
`p2p/protocol_version.py`). Core's own 31799 is under either, so the wire
half passes on both builds. The version boundary passes on PyPI's
`2026.10.4` and on `main` (`6777a6a8`); `2026.9.24` closes the connection
of its 70015 peer, under its floor, so the body fails there.

The log half does not: `Capability.DEBUG_LOG` is not declared
(`btclib_node.py`'s own `capabilities`), this node's own log carrying no
sentence Core's wording would match, so the second test skips.

    export TF2_INTEGRATION=1 TF2_BTCLIB_NODE_PYTHON=<python>
    uv run pytest tests/integration/p2p_leak_btclib_node_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.p2p_leak_test import (
    feature_negotiation_starts_at_the_wtxid_version,
    obsolete_version_disconnects_the_peer,
    obsolete_version_is_logged,
)

if TYPE_CHECKING:
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_obsolete_version_disconnects_the_peer(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the wire half the body module names, over btclib-node."""
    obsolete_version_disconnects_the_peer(btclib_node_adapter)


def test_obsolete_version_is_logged(
    btclib_node_adapter: BtclibNodeAdapter, skip_counts: SkipCounts
) -> None:
    """The target: skipped, this node's own log carrying no such wording."""
    obsolete_version_is_logged(btclib_node_adapter, skip_counts)


def test_feature_negotiation_starts_at_the_wtxid_version(
    btclib_node_adapter: BtclibNodeAdapter,
) -> None:
    """The target: the version boundary the body module names."""
    feature_negotiation_starts_at_the_wtxid_version(btclib_node_adapter)
