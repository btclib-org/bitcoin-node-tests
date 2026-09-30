# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `p2p_getaddr_caching`, rewritten on this repository's harness.

Read from Core's `test/functional/p2p_getaddr_caching.py`:
`p2p_getaddr_caching_test.py` beside this module is the body, run here
against bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.p2p_getaddr_caching_test import (
    getaddr_answers_are_cached_per_bind,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


class _UnboundBitcoindAdapter(BitcoindAdapter):
    """`BitcoindAdapter` without the `-bind` its `_command` names.

    Core's node listens on the onion binds its test names beside its
    framework's loopback one. An `extra_args` entry cannot add a
    `-bind` beside the adapter's own, `NodeAdapter` refusing one naming an
    option `_command()` already sets, so the entry is left out where it is
    set.
    """

    @override
    def _command(self) -> list[str]:
        """Return the base command without its `-bind`."""
        return [arg for arg in super()._command() if not arg.startswith("-bind=")]


def test_getaddr_answers_are_cached_per_bind(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: one cached `getaddr` answer per bind, over bitcoind."""
    getaddr_answers_are_cached_per_bind(
        make_adapter, _UnboundBitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
