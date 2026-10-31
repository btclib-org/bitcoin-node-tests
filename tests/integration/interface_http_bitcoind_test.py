# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_http`, its excessive request size step: bitcoind.

Read from Core's `test/functional/interface_http.py`:
`interface_http_test.py` beside this module is the body, run here against
bitcoind, which declares every capability it asks for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.interface_http_test import (
    excessive_request_size_is_logged,
    excessive_request_size_is_refused,
)

if TYPE_CHECKING:
    from btclib_functional_tests.bitcoind import BitcoindAdapter
    from btclib_functional_tests.capability import SkipCounts

pytestmark = pytest.mark.integration


def test_excessive_request_size_is_refused(
    bitcoind_adapter: BitcoindAdapter,
) -> None:
    """The oracle: the wire half the body module names, over bitcoind."""
    excessive_request_size_is_refused(bitcoind_adapter)


def test_excessive_request_size_is_logged(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The oracle: the log half the body module names, over bitcoind."""
    excessive_request_size_is_logged(bitcoind_adapter, skip_counts)
