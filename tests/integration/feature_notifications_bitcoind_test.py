# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_notifications`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_notifications.py`:
`feature_notifications_test.py` beside this module has the bodies, run
here against bitcoind, which declares every capability they ask for.
Which wording of the warning about an invalid chain with more work the
body expects is read from the running build's own `getnetworkinfo`
`version` ([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)),
`_names_the_invalid_chain` below having which builds use which.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_notifications_test import (
    a_large_work_invalid_chain_is_alerted,
    every_new_tip_is_notified,
    the_shutdown_is_notified,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# the `CLIENT_VERSION` (`src/clientversion.h`) `master` reports from its
# move to `30.99` (`314c42b55b`, 2025-09-09): every release from
# `v31.0rc1` on names the invalid chain in its warning, and `master` does
# from `2c44c41984` (2025-12-09) on
_FIRST_VERSION_NAMING_THE_INVALID_CHAIN = 309900


def _names_the_invalid_chain(node: NodeAdapter) -> bool:
    """Say whether the running build warns in Core's own wording.

    A known limit: a `master` build from the version's move to `30.99`
    until `2c44c41984` reports `309900` and warns that it does not fully
    agree with its peers all the same, so the test fails against such a
    build. `30.99`'s own merges before `2c44c41984` are fewer than those
    after it, which a threshold at `310000` would get wrong instead.
    """
    version = node.rpc.call("getnetworkinfo")["version"]
    assert isinstance(version, int)
    return version >= _FIRST_VERSION_NAMING_THE_INVALID_CHAIN


def test_every_new_tip_is_notified(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-blocknotify`'s command run per block, over bitcoind."""
    every_new_tip_is_notified(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_a_large_work_invalid_chain_is_alerted(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the invalid chain's warning notified, over bitcoind."""
    a_large_work_invalid_chain_is_alerted(
        make_adapter,
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        skip_counts,
        _names_the_invalid_chain,
    )


def test_the_shutdown_is_notified(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: `-shutdownnotify`'s command run on stop, over bitcoind."""
    the_shutdown_is_notified(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
