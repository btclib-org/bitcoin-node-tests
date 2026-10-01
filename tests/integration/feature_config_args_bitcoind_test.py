# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_config_args`, rewritten on this harness: bitcoind.

`feature_config_args_test.py` beside this module holds each body, run here
against bitcoind. A build before `v31.0` has no `-privatebroadcast`, and
that body is a counted skip on `Capability.PRIVATE_BROADCAST` there.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from tests.integration.feature_config_args_test import (
    a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy,
    a_proxy_without_a_value_is_refused,
    private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_proxy_without_a_value_is_refused(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_proxy_without_a_value_is_refused(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )


def test_private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The oracle: the body this module's docstring names, over bitcoind."""
    private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing(
        make_adapter, BitcoindAdapter, bitcoind_path, tmp_path, skip_counts
    )
