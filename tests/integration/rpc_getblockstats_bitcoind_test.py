# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getblockstats`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getblockstats.py` (`b7cbd804284b`,
2026-05-25) and narrowed to what the MiniWallet and disk families reach
together
([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)):
`MiniWallet.create_self_transfer`/`generate` (`Capability.MINE`) build a
chain carrying an `OP_RETURN` output, `btclib.coinstats.bogo_size` -- the
same function `feature_utxo_set_hash_bitcoind_test.py`'s own `CoinStats`
calls -- computes what `getblockstats`'s own `utxo_size_inc*` fields
answer independently rather than trusting a hard-coded literal, and a
direct read of `blk00000.dat` (`Capability.BLK_FILES`) under the node's
own datadir is disk's own contribution: renaming it away is what makes
`getblockstats` answer "Block not found on disk". `Capability.BLOCK_STATS`
gates every subject here: `getblockstats` names no callback in
`btclib-node`'s own dispatch table (`btclib_node.py`'s own docstring),
so nothing here ever reaches that node.

Not the clock family, unlike Core's own file: an ordinary run of Core's
calls `setmocktime` only in `load_test_data`, so that a node replaying
its fixture's old blocks leaves Initial Block Download; this port mines
fresh blocks with `MiniWallet` rather than replaying that fixture, so
nothing here waits on the freeze.

A smaller claim than Core's own file: kept is the genesis block's own
statistics (independently computed rather than copied from Core's own
literals, the genesis block being a network constant this harness's own
chain shares with Core's) and the same answer when the block is selected
by hash; that an `OP_RETURN` output is counted in
`utxo_increase`/`utxo_size_inc` but excluded from
`utxo_increase_actual`/`utxo_size_inc_actual`; that `stats=[...]`
narrows the answer to exactly the names given; the height-out-of-range
and negative-height error messages; the invalid-statistic-name error
message, for the invalid name alone, beside a valid one on either side
of it or between two, and prefixed; mainnet's genesis hash answering
`Block not found`; the required-argument usage string; and the disk
read. Dropped is Core's own vendored `data/rpc_getblockstats.json`
fixture and every comparison it feeds -- the full key set, the heights
and each statistic of the blocks it replays, by height and by hash (a
generated file this harness would have to regenerate against its own
chain to mean anything) -- its per-stat query loop over those same
blocks, and its `submitheader`-only-known-block case (this harness's own
adapter has no `submitheader` wrapper).

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.block import genesis_block
from btclib.block.block import Block
from btclib.coinstats import bogo_size
from btclib.tx import TxOut
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet, nulldata_script_pub_key
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from pathlib import Path

    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

pytestmark = pytest.mark.integration

_GENESIS_COINBASE_SPK = genesis_block("regtest").transactions[0].vout[0].script_pub_key
_GENESIS_BOGO_SIZE = bogo_size(_GENESIS_COINBASE_SPK.script)


def test_genesis_block_statistics(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Genesis is a network constant: its own stats need no chain of ours."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    stats = bitcoind_adapter.rpc.call("getblockstats", [0])
    assert stats["blockhash"] == genesis_block("regtest").header.hash.hex()
    assert bitcoind_adapter.rpc.call("getblockstats", [stats["blockhash"]]) == stats
    assert stats["utxo_increase"] == 1
    assert stats["utxo_size_inc"] == _GENESIS_BOGO_SIZE
    # spendable-looking and unspendable (btclib.coinstats's own module
    # docstring): the real UTXO set never gains genesis's own coinbase
    assert stats["utxo_increase_actual"] == 0
    assert stats["utxo_size_inc_actual"] == 0


def test_op_return_is_counted_but_not_actual(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An OP_RETURN output inflates utxo_increase but not its actual twin."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    require(Capability.MINE, bitcoind_adapter.capabilities, skip_counts)
    wallet = MiniWallet(bitcoind_adapter)
    wallet.generate(COINBASE_MATURITY + 1)
    tx = wallet.create_self_transfer()
    tx.vout.append(TxOut(0, nulldata_script_pub_key(b"\x21")))
    bitcoind_adapter.rpc.call(
        "sendrawtransaction", [tx.serialize(True, check_validity=False).hex()]
    )
    (block_hash,) = wallet.generate(1, confirm=[tx])
    tip = bitcoind_adapter.rpc.call("getblockcount")
    block_hex = bitcoind_adapter.rpc.call("getblock", [block_hash.hex(), 0])
    block = Block.parse(bytes.fromhex(block_hex), check_validity=False)

    stats = bitcoind_adapter.rpc.call("getblockstats", [tip])
    assert stats["blockhash"] == block_hash.hex()
    # coinbase reward, its own witness commitment, the change output and
    # the nulldata output, minus the one coin the transaction spends: 4
    # outs, 1 in, not discounting either unspendable output
    assert stats["utxo_increase"] == 3
    # the witness commitment and the nulldata output are both unspendable,
    # so only the reward and the change count -- 2 outs, 1 in
    assert stats["utxo_increase_actual"] == 1
    p2tr_bogo_size = bogo_size(wallet.script_pub_key.script)
    # every output the block adds, spendable or not, minus the coin spent
    added = sum(
        bogo_size(out.script_pub_key.script)
        for block_tx in block.transactions
        for out in block_tx.vout
    )
    assert stats["utxo_size_inc"] == added - p2tr_bogo_size
    # reward and change are both p2tr, the same shape as the coin spent:
    # two added and one removed nets exactly one p2tr's own bogo size
    assert stats["utxo_size_inc_actual"] == p2tr_bogo_size


def test_selected_stats_narrow_the_answer(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """stats=[...] returns exactly the names asked for, nothing else."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    result = bitcoind_adapter.rpc.call("getblockstats", [0, ["minfee", "maxfee"]])
    assert set(result.keys()) == {"minfee", "maxfee"}


def test_height_out_of_range(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """A height past the tip, and a negative one, are both refused."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    tip = bitcoind_adapter.rpc.call("getblockcount")
    with pytest.raises(
        RpcError, match=f"Target block height {tip + 1} after current tip {tip}"
    ):
        bitcoind_adapter.rpc.call("getblockstats", [tip + 1])
    with pytest.raises(RpcError, match="Target block height -1 is negative"):
        bitcoind_adapter.rpc.call("getblockstats", [-1])


def test_invalid_statistic_name(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """An unknown statistic name is refused by name, wherever it sits."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    invalid = "asdfghjkl"
    for selected in (
        [invalid],
        ["minfee", invalid],
        [invalid, "minfee"],
        ["minfee", invalid, "maxfee"],
    ):
        with pytest.raises(RpcError, match=f"Invalid selected statistic '{invalid}'"):
            bitcoind_adapter.rpc.call("getblockstats", [0, selected])
    # the name refused is the one given, not a fixed culprit
    with pytest.raises(RpcError, match=f"Invalid selected statistic 'aaa{invalid}'"):
        bitcoind_adapter.rpc.call("getblockstats", [0, ["minfee", f"aaa{invalid}"]])


def test_unknown_block_hash(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Mainnet's genesis block is not a block this regtest chain holds."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    mainnet_genesis = genesis_block("mainnet").header.hash.hex()
    with pytest.raises(RpcError, match="Block not found"):
        bitcoind_adapter.rpc.call("getblockstats", [mainnet_genesis])


def test_required_args(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """The wrong argument count is refused with the usage string."""
    require(Capability.BLOCK_STATS, bitcoind_adapter.capabilities, skip_counts)
    with pytest.raises(RpcError, match="getblockstats"):
        bitcoind_adapter.rpc.call("getblockstats")
    with pytest.raises(RpcError, match="getblockstats"):
        bitcoind_adapter.rpc.call("getblockstats", ["00", 1, 2])


def test_block_not_found_on_disk(
    make_adapter: AdapterFactory,
    bitcoind_path: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """A `blk00000.dat` moved away from under the node is a disk-level miss."""
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(BitcoindAdapter, bitcoind_path, tmp_path, rpc_port, p2p_port)
    adapter.start()
    try:
        require(Capability.BLOCK_STATS, adapter.capabilities, skip_counts)
        require(Capability.BLK_FILES, adapter.capabilities, skip_counts)
        blk_file = tmp_path / "regtest" / "blocks" / "blk00000.dat"
        backup = blk_file.with_suffix(".dat.backup")
        blk_file.rename(backup)
        try:
            with pytest.raises(RpcError, match="Block not found on disk"):
                adapter.rpc.call("getblockstats", [0])
        finally:
            backup.rename(blk_file)
    finally:
        adapter.stop()
