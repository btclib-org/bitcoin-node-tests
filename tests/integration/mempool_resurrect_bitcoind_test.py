# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `mempool_resurrect`, on tf2's own harness: bitcoind.

Read from Core's `test/functional/mempool_resurrect.py` (`fa5f29774872`,
2025-12-16) rather than ported: that file spends coinbases into two mined
blocks, then submits an empty fork -- `test_framework.blocktools`'s own
`create_empty_fork`, built before either of those two -- reorging both
away, and checks the spends land back in the mempool before a further
block confirms them again. This asks the same question -- do transactions
a reorg orphans return to the mempool, and get mined again once a new tip
accepts them -- with `MiniWallet.build_fork` (`mini_wallet.py`) standing in
for `create_empty_fork`, a narrower fork than Core's own arbitrary margin
(this module's own `_FORK_LENGTH`, only as long as it needs to outnumber
what this test also mines meanwhile), `MiniWallet.generate`'s own
`confirm` standing in for Core's node-side mining pulling the whole
mempool in (this class reads no mempool back, `mini_wallet.py`'s own
docstring has why), and `MiniWallet.resync` picking up the reorged tip
afterwards: this class has no `scantxoutset` to rebuild its coin cache
from, so nothing here calls `rescan_utxos` either.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, build_fork

if TYPE_CHECKING:
    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# long enough to outweigh the blocks mined between building this fork and
# submitting it: Core's own file carries a fixed, arbitrary margin over
# the same two, and this margin clears the same requirement
_FORK_LENGTH = 3

# how many coins to mine and then spend, matching Core's own file: enough
# for a fork reorg to have something on both sides of it to resurrect
_SPEND_COUNT = 3


def test_a_reorg_returns_spent_coinbases_to_the_mempool(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Core's own subject: an orphaned block's txs resurrect, then reconfirm."""
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    # enough mature coins for every spend below, all mined before the
    # fork's own base -- so the fork itself never conflicts with any of
    # them
    wallet.generate(100 + 2 * _SPEND_COUNT)
    fork = build_fork(bitcoind_adapter, wallet.script_pub_key, _FORK_LENGTH)

    first_spends = [wallet.send_self_transfer() for _ in range(_SPEND_COUNT)]
    first_block = wallet.generate(1, confirm=first_spends)[0]
    second_spends = [wallet.send_self_transfer() for _ in range(_SPEND_COUNT)]
    second_block = wallet.generate(1, confirm=second_spends)[0]
    spends = first_spends + second_spends
    spend_ids = {tx.id.hex() for tx in spends}

    # confirmed, not left pending -- checked against this test's own ids
    # rather than mempool emptiness, the session-scoped node being shared
    # with every other MiniWallet test
    mempool_before_reorg = set(bitcoind_adapter.rpc.call("getrawmempool"))
    assert not (spend_ids & mempool_before_reorg)
    confirmed = set(bitcoind_adapter.rpc.call("getblock", [first_block.hex()])["tx"])
    confirmed |= set(bitcoind_adapter.rpc.call("getblock", [second_block.hex()])["tx"])
    assert spend_ids <= confirmed

    # bitcoind's own `submitblock` answers "inconclusive" for a fork block
    # it accepts but does not fully validate, not yet knowing whether the
    # fork will end up the best chain; null is what it answers once one
    # does. Core's own file does not check these either, only the final
    # tip below
    for block in fork:
        answer = bitcoind_adapter.rpc.call(
            "submitblock", [block.serialize(check_validity=False).hex()]
        )
        assert answer in {None, "inconclusive"}
    assert bitcoind_adapter.rpc.call("getbestblockhash") == fork[-1].header.hash.hex()

    # resurrected: the reorg orphaned both blocks above, and neither spend
    # conflicts with anything the fork itself carries
    mempool_after_reorg = set(bitcoind_adapter.rpc.call("getrawmempool"))
    assert spend_ids <= mempool_after_reorg

    wallet.resync()
    final_block = wallet.generate(1, confirm=spends)[0]

    mempool_after_confirm = set(bitcoind_adapter.rpc.call("getrawmempool"))
    assert not (spend_ids & mempool_after_confirm)
    confirmed_again = set(
        bitcoind_adapter.rpc.call("getblock", [final_block.hex()])["tx"]
    )
    assert spend_ids <= confirmed_again
