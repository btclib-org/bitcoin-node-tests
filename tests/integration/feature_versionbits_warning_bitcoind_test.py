# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_versionbits_warning`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_versionbits_warning.py`:
`feature_versionbits_warning_test.py` beside this module is the body, run
here against bitcoind, which declares every capability it asks for.
Whether the body expects no warning for a bit BIP323 reserves is read
from the running build's own `getnetworkinfo` `version`
([ISS 35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)),
`_ignores_reserved_bits` below having which builds do.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_versionbits_warning_test import (
    unknown_rules_raise_a_warning,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

# the last tag of each maintenance branch whose own `VERSIONBITS_NUM_BITS`
# (`src/versionbits.h`) predates BIP323, the branch carrying it past
# that tag, as major to minor of Core's own `CLIENT_VERSION`
# (`src/clientversion.h`)
_LAST_TAG_BEFORE_BIP323 = {30: 3, 31: 1}

# `master`'s own minor, and the first major whose `master` carries BIP323
# (`5bd990a3dd`, 2026-06-03)
_MASTER_MINOR = 99
_FIRST_MASTER_WITH_BIP323 = 31

# the first major whose every tag carries BIP323, `v32.0rc1` on
_FIRST_MAJOR_WITH_BIP323 = 32


def _ignores_reserved_bits(node: NodeAdapter) -> bool:
    """Say whether the running build warns for no bit BIP323 reserves.

    A known limit: a `master` build from the version's move to `31.99`
    (`b97abdcdf1`, 2026-03-10) until BIP323's merge reports `319900` and
    warns all the same, so the test fails against such a build.
    """
    version = node.rpc.call("getnetworkinfo")["version"]
    assert isinstance(version, int)
    major, minor = divmod(version // 100, 100)
    if minor == _MASTER_MINOR:
        return major >= _FIRST_MASTER_WITH_BIP323
    if major >= _FIRST_MAJOR_WITH_BIP323:
        return True
    last = _LAST_TAG_BEFORE_BIP323.get(major)
    return last is not None and minor > last


def test_unknown_rules_raise_a_warning(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: unknown rules activated warned about, over bitcoind."""
    unknown_rules_raise_a_warning(
        make_adapter,
        BitcoindAdapter,
        bitcoind_path,
        tmp_path,
        skip_counts,
        _ignores_reserved_bits,
    )
