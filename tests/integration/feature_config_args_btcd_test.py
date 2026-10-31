# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_config_args`, rewritten on tf2's own harness: btcd.

`feature_config_args_test.py` beside this module is the body, run here
against btcd, a target rather than the oracle (rule 3 of issue
btclib-org/btclib#2220).

    export TF2_INTEGRATION=1 TF2_BTCD=<btcd>
    uv run pytest tests/integration/feature_config_args_btcd_test.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from btclib_functional_tests.btcd import BtcdAdapter
from tests.integration.feature_config_args_test import (
    a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy,
    a_proxy_without_a_value_is_refused,
    private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing,
)

if TYPE_CHECKING:
    from pathlib import Path

    from btclib_functional_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration


def test_a_proxy_without_a_value_is_refused(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_proxy_without_a_value_is_refused(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    a_connect_node_ignores_the_seednode_and_the_dnsseed_beside_a_proxy(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )


def test_private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing(
    make_adapter: AdapterFactory,
    btcd_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """The target: the body this module's docstring names, over btcd."""
    private_broadcast_is_refused_without_a_proxy_and_warns_without_randomizing(
        make_adapter, BtcdAdapter, btcd_path, tmp_path, skip_counts
    )
