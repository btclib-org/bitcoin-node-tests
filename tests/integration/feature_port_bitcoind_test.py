# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_port`, rewritten on this repository's harness.

Read from Core's `test/functional/feature_port.py`:
`feature_port_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_port_test import (
    port_and_bind_decide_where_the_node_listens,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


class _UnboundBitcoindAdapter(BitcoindAdapter):
    """`BitcoindAdapter` without the `-bind` its `_command` names.

    Core's test sets `bind_to_localhost_only` off and `has_explicit_bind`
    on, so that the test names where the node listens. An `extra_args`
    entry cannot replace the adapter's own `-bind`, `NodeAdapter`
    refusing one naming an option `_command()` already sets, so the entry
    is left out where it is set.
    """

    @override
    def _command(self) -> list[str]:
        """Return the base command without its `-bind`."""
        return [arg for arg in super()._command() if not arg.startswith("-bind=")]


def test_port_and_bind_decide_where_the_node_listens(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: where `-port` and `-bind` have bitcoind listen."""
    port_and_bind_decide_where_the_node_listens(
        make_adapter, _UnboundBitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
