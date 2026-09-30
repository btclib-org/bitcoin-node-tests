# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_maxtipage`, one body over either node.

Read from Core's `test/functional/feature_maxtipage.py`
(`fa5f29774872`, 2025-12-16), an option and the clock beside
node-linking
([ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
a node restarted with `-maxtipage` (`Capability.MAX_TIP_AGE`) and
connected to a miner stays in initial block download while every block
it receives is older than the maximum age by its clock, and leaves it on
the first block exactly that old. Core runs it for the default of a day,
passing no option, for each of its hour values, and for the largest
value the option takes, where only the block leaving initial block
download is mined.

Core's `generate` has the miner build each block itself, on the clock
Core's `setmocktime` just gave it. Here the block is built by
`build_next_block` (`mini_wallet.py`), stamped with that clock's time
and submitted over `submitblock` (`Capability.MINE`), its coinbase
paying `RAW_P2PK_SCRIPT_PUB_KEY` rather than Core's deterministic
address. The miner's clock is set as Core sets it. For the largest
value Core's `setmocktime` is given `0`, which puts the miner back on
the wall clock, and the block takes `build_next_block`'s own default
time, the wall clock or one second past the median-time-past, whichever
is later.

`feature_maxtipage_bitcoind_test.py` and
`feature_maxtipage_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import RAW_P2PK_SCRIPT_PUB_KEY, build_next_block
from bitcoin_node_tests.node import connect_nodes, sync_all

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = ["ibd_ends_at_the_max_tip_age"]

# Core's own `DEFAULT_MAX_TIP_AGE` (`src/kernel/chainstatemanager_opts.h`)
_DEFAULT_MAX_TIP_AGE = 24 * 60 * 60

# the hour values Core's `run_test` passes, in its order
_HOURS = (20, 10, 5, 2, 1)

# the largest value Core's `run_test` passes, `int64_t`'s own maximum
_MAX_LONG_VAL = 9223372036854775807

# how many seconds past the maximum age Core's older blocks are, in order
_DELTAS = (5, 4, 3, 2, 1)


def _in_ibd(node: NodeAdapter) -> bool:
    """Return `getblockchaininfo`'s own `initialblockdownload`."""
    info = node.rpc.call("getblockchaininfo")
    assert isinstance(info, dict)
    in_ibd = info["initialblockdownload"]
    assert isinstance(in_ibd, bool)
    return in_ibd


def _generate(miner: NodeAdapter, ibd: NodeAdapter, block_time: int | None) -> None:
    """Core's own `self.generate(node_miner, 1)`, then its `sync_all`.

    :param miner: the node the block is submitted to.
    :param ibd: the node the block is relayed to.
    :param block_time: the block's own time, or `None` for
        `build_next_block`'s own default.
    """
    block = build_next_block(miner, RAW_P2PK_SCRIPT_PUB_KEY, time=block_time)
    answer = miner.rpc.call(
        "submitblock", [block.serialize(check_validity=False).hex()]
    )
    assert answer is None
    sync_all([miner, ibd])


def _test_maxtipage(
    miner: NodeAdapter,
    ibd: NodeAdapter,
    maxtipage: int,
    *,
    set_parameter: bool = True,
    test_deltas: bool = True,
) -> None:
    """Core's own `test_maxtipage`, over the same pair of nodes.

    :param miner: Core's `node_miner`.
    :param ibd: Core's `node_ibd`, restarted here.
    :param maxtipage: the maximum tip age, in seconds.
    :param set_parameter: whether the restart passes `-maxtipage`.
    :param test_deltas: whether blocks older than `maxtipage` are mined
        first.
    """
    ibd.restart([f"-maxtipage={maxtipage}"] if set_parameter else None)
    connect_nodes(miner, ibd)
    cur_time = int(time.time())

    if test_deltas:
        # tips older than maximum age -> stay in IBD
        ibd.set_mock_time(cur_time)
        for delta in _DELTAS:
            block_time = cur_time - maxtipage - delta
            miner.set_mock_time(block_time)
            _generate(miner, ibd, block_time)
            assert _in_ibd(ibd) is True

    # tip within maximum age -> leave IBD
    mock_time = max(cur_time - maxtipage, 0)
    miner.set_mock_time(mock_time)
    _generate(miner, ibd, mock_time or None)
    assert _in_ibd(ibd) is False

    # the miner back on the wall clock, as Core's own test leaves it
    miner.set_mock_time(0)


def ibd_ends_at_the_max_tip_age(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's own `run_test`: IBD ends at the first tip within `-maxtipage`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    miner, ibd = cluster(2)
    require(Capability.MAX_TIP_AGE, ibd.capabilities, skip_counts)
    require(Capability.CLOCK, ibd.capabilities, skip_counts)
    require(Capability.CLOCK, miner.capabilities, skip_counts)
    require(Capability.MINE, miner.capabilities, skip_counts)
    require(Capability.CONNECT, miner.capabilities, skip_counts)

    _test_maxtipage(miner, ibd, _DEFAULT_MAX_TIP_AGE, set_parameter=False)

    for hours in _HOURS:
        _test_maxtipage(miner, ibd, hours * 60 * 60)

    _test_maxtipage(miner, ibd, _MAX_LONG_VAL, test_deltas=False)
