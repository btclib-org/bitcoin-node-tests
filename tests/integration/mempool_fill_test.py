# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`fill_mempool`, one body over either node.

Read from Core's `test/functional/test_framework/mempool_util.py`
(`fa5f29774872`, 2025-12-16). Core's own two callers,
`mempool_package_rbf.py` and `rpc_packages.py`, each start their node
with `-maxmempool=5`; this body restarts its node the same way, over
`Capability.MAXMEMPOOL`, and asserts what `fill_mempool` itself already
asserts before returning -- `mempoolminfee` above `minrelaytxfee`, and
the low fee-rate transaction it sent first gone from the mempool --
rather than repeating either check.

`mempool_fill_bitcoind_test.py` and `mempool_fill_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mempool_util import fill_mempool

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = ["fill_mempool_evicts_its_own_low_fee_rate_transaction"]


def fill_mempool_evicts_its_own_low_fee_rate_transaction(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check `fill_mempool` returns having raised nothing: the node evicted.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.MAXMEMPOOL, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    node.restart(["-maxmempool=5"])
    fill_mempool(node)
