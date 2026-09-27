# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_generate`, one body over either node.

Read from Core's `test/functional/rpc_generate.py` (`6eca11175be6`,
2026-07-16): the node builds and solves blocks itself, over
`generatetoaddress` and `generateblock` (`Capability.GENERATE`), paying
an address or a descriptor and carrying exactly the transactions it is
handed, and answers the hidden `generate` with the message naming the
`-generate` option that replaces it. Each of Core's own subtests is a
function here, run on a node of its own, and every assertion Core's file
makes is kept, the addresses, descriptors and messages copied from it.

`MiniWallet` (`Capability.MINE`) is Core's own too: its address is what
`generateblock` pays, and its self-transfers are the transactions a
block is asked to carry. It needs coins, so it mines
`COINBASE_MATURITY` blocks of its own first, where Core's own node
starts on a chain its framework already mined; its blocks are
client-built over `submitblock`, and the blocks under test are the
node's own.

Where Core's own file goes through `bitcoin-cli`, this one cannot. Core
calls `generateblock` from several threads over `bitcoin-cli`, a program
this repository does not run; here as many threads each hold an RPC
client of their own (`NodeAdapter.rpc`), concurrency being the subject.
And Core asks for `generate`'s own refusal and help only where its run
does not go through `bitcoin-cli` (`self.options.usecli`); an RPC client
is the only way this repository reaches a node, so both are asked
always.

`rpc_generate_bitcoind_test.py` and `rpc_generate_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.tx.limits import COINBASE_MATURITY

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.mini_wallet import MiniWallet

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from bitcoin_node_tests.node import NodeAdapter

__all__ = [
    "generate_is_a_hidden_command_naming_the_cli_option",
    "generateblock_mines_what_it_is_handed",
    "generatetoaddress_refuses_another_chain_s_address",
]

# `src/rpc/protocol.h`'s own codes for the refusals asserted below
_METHOD_NOT_FOUND = -32601
_INVALID_PARAMETER = -8
_DESERIALIZATION = -22
_VERIFY_ERROR = -25
_INVALID_ADDRESS_OR_KEY = -5

# Core's own `test_generate` message
_GENERATE_MESSAGE = (
    "generate\n\n"
    "has been replaced by the -generate "
    "cli option. Refer to -help for more information.\n"
)

# Core's own addresses and keys, copied from its file
_TESTNET_ADDRESS = "mneYUmWYsuk7kySiURxCi3AGxrAqZxLgPZ"
_MAINNET_ADDRESS = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
_COMBO_KEY_COMPRESSED = (
    "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
)
_COMBO_ADDRESS_COMPRESSED = "bcrt1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
_COMBO_KEY_UNCOMPRESSED = (
    "0408ef68c46d20596cc3f6ddf7c8794f71913add807f1dc55949fa805d764d191c"
    "0b7ce6894c126fce0babc6663042f3dde9b0cf76467ea315514e5a6731149c67"
)
_COMBO_ADDRESS_UNCOMPRESSED = "mkc9STceoCcjoXEXe6cm66iJbmjM6zR9B2"
_TPUB = (
    "tpubD6NzVbkrYhZ4XgiXtGrdW5XDAPFCL9h7we1vwNCpn8tGbBcgfVYjXyhWo4E1xkh56hjod1Rh"
    "GjxbaTLV3X4FyWuejifB9jusQ46QzG87VKp"
)
_RANGED_DESCRIPTOR = f"pkh({_TPUB}/0/*)"
_HARDENED_CHILD_DESCRIPTOR = f"pkh({_TPUB}/0'/0)"

# Core's own self-transfers left in the mempool, its threads, and the
# blocks each thread asks for
_UNMINED = 10
_THREADS = 6
_BLOCKS_PER_THREAD = 50

# coins `MiniWallet` needs mature: the unmined self-transfers, the one
# `generateblock` is handed by txid, and the out-of-order parent
_COINS = _UNMINED + 2


def _refused(
    node: NodeAdapter,
    method: str,
    params: Sequence[object] | dict[str, object],
    code: int,
    message: str,
) -> None:
    """Assert `method` is refused, as Core's `assert_raises_rpc_error` asserts.

    :param code: the node's own error code, `src/rpc/protocol.h`.
    :param message: a substring of the node's own error message.
    """
    with pytest.raises(RpcError) as refusal:
        node.rpc.call(method, params)
    assert refusal.value.code == code, (method, str(refusal.value))
    assert message in refusal.value.args[0], (method, str(refusal.value))


def _single_output_address(node: NodeAdapter, block_hash: str) -> str:
    """Assert `block_hash` holds its coinbase alone; return what that pays."""
    block = node.rpc.call("getblock", [block_hash, 2])
    assert len(block["tx"]) == 1
    address = block["tx"][0]["vout"][0]["scriptPubKey"]["address"]
    assert isinstance(address, str)
    return address


def generatetoaddress_refuses_another_chain_s_address(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `test_generatetoaddress`: a testnet address mines, mainnet's not.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    (block_hash,) = node.rpc.call("generatetoaddress", [1, _TESTNET_ADDRESS])
    assert node.rpc.call("getbestblockhash") == block_hash
    _refused(
        node,
        "generatetoaddress",
        [1, _MAINNET_ADDRESS],
        _INVALID_ADDRESS_OR_KEY,
        "Invalid address",
    )


def generate_is_a_hidden_command_naming_the_cli_option(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `test_generate`: refused, helped, and missing from the list.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    _refused(node, "generate", [], _METHOD_NOT_FOUND, _GENERATE_MESSAGE)
    assert node.rpc.call("help", ["generate"]) == _GENERATE_MESSAGE
    assert _GENERATE_MESSAGE not in node.rpc.call("help")


def generateblock_mines_what_it_is_handed(
    cluster: Callable[[int], Sequence[BitcoindAdapter | BtclibNodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Core's `test_generateblock`, in its order.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.GENERATE, node.capabilities, skip_counts)
    require(Capability.MINE, node.capabilities, skip_counts)
    wallet = MiniWallet(node)
    wallet.generate(COINBASE_MATURITY + _COINS)
    address = wallet.script_pub_key.address

    # an empty block to an address, returned unsubmitted and then submitted
    generated = node.rpc.call(
        "generateblock", {"output": address, "transactions": [], "submit": False}
    )
    assert node.rpc.call("submitblock", {"hexdata": generated["hex"]}) is None
    assert generated["hash"] == node.rpc.call("getbestblockhash")

    # an empty block to an address, and to the same address as a descriptor
    block_hash = node.rpc.call(
        "generateblock", {"output": address, "transactions": []}
    )["hash"]
    block = node.rpc.call("getblock", {"blockhash": block_hash, "verbose": 2})
    assert len(block["tx"]) == 1
    assert block["tx"][0]["vout"][0]["scriptPubKey"]["address"] == address
    block_hash = node.rpc.call("generateblock", [f"addr({address})", []])["hash"]
    block = node.rpc.call("getblock", {"blockhash": block_hash, "verbosity": 2})
    assert len(block["tx"]) == 1
    assert block["tx"][0]["vout"][0]["scriptPubKey"]["address"] == address

    # an empty block to a combo descriptor, compressed key and uncompressed
    for key, expected in (
        (_COMBO_KEY_COMPRESSED, _COMBO_ADDRESS_COMPRESSED),
        (_COMBO_KEY_UNCOMPRESSED, _COMBO_ADDRESS_UNCOMPRESSED),
    ):
        block_hash = node.rpc.call("generateblock", [f"combo({key})", []])["hash"]
        assert _single_output_address(node, block_hash) == expected

    # transactions left in the mempool, which no block below is handed
    for _ in range(_UNMINED):
        wallet.send_self_transfer()

    # a block handed a txid from the mempool carries it, and nothing else
    txid = wallet.send_self_transfer().id.hex()
    block_hash = node.rpc.call("generateblock", [address, [txid]])["hash"]
    block = node.rpc.call("getblock", [block_hash, 1])
    assert len(block["tx"]) == 2
    assert block["tx"][1] == txid

    # a block handed a raw transaction carries it, byte for byte
    rawtx = wallet.create_self_transfer().serialize(True, check_validity=False).hex()
    block_hash = node.rpc.call("generateblock", [address, [rawtx]])["hash"]
    block = node.rpc.call("getblock", [block_hash, 1])
    assert len(block["tx"]) == 2
    mined = node.rpc.call(
        "getrawtransaction",
        {"txid": block["tx"][1], "verbose": False, "blockhash": block_hash},
    )
    assert mined == rawtx

    # many threads at once, each over an RPC client of its own
    def generate_blocks(_: int) -> None:
        rpc = node.rpc
        for _ in range(_BLOCKS_PER_THREAD):
            rpc.call("generateblock", {"output": address, "transactions": []})

    with ThreadPoolExecutor(max_workers=_THREADS) as threads:
        list(threads.map(generate_blocks, range(_THREADS)))

    # a child ahead of its own parent
    parent = wallet.send_self_transfer()
    coin = wallet.get_utxo(txid=parent.id.hex())
    child = wallet.create_self_transfer(utxo_to_spend=coin)
    _refused(
        node,
        "generateblock",
        [address, [child.serialize(True, check_validity=False).hex(), parent.id.hex()]],
        _VERIFY_ERROR,
        "TestBlockValidity failed: bad-txns-inputs-missingorspent",
    )

    missing_txid = "00" * 32
    _refused(
        node,
        "generateblock",
        [address, [missing_txid]],
        _INVALID_ADDRESS_OR_KEY,
        f"Transaction {missing_txid} not in mempool.",
    )
    _refused(
        node,
        "generateblock",
        [address, ["0000"]],
        _DESERIALIZATION,
        "Transaction decode failed for 0000",
    )
    _refused(
        node,
        "generateblock",
        ["1234", []],
        _INVALID_ADDRESS_OR_KEY,
        "Invalid address or descriptor",
    )
    _refused(
        node,
        "generateblock",
        [_RANGED_DESCRIPTOR, []],
        _INVALID_PARAMETER,
        "Ranged descriptor not accepted. Maybe pass through deriveaddresses first?",
    )
    _refused(
        node,
        "generateblock",
        [_HARDENED_CHILD_DESCRIPTOR, []],
        _INVALID_ADDRESS_OR_KEY,
        "Cannot derive script without private keys",
    )
