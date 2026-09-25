# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BtclibNodeAdapter`: the first target, `btclib-node` over `python -m`.

[btclib-node PR 1012](https://github.com/btclib-org/btclib-node/pull/1012)
is what this adapter needs already served: `getblock`, `submitblock`,
`addnode` and `getnetworkinfo`, measured present in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table before this
module was written.

`Capability.MINE` is not declared, and this is the finding rather than a
gap this adapter papers over: a solo `btclib-node`, with no peer, never
leaves `NodeStatus.SyncingHeaders` (`src/btclib_node/__init__.py`'s own
`run`), and `main.update_chain`'s own `_ready_fork` refuses to connect
anything -- a block this adapter submits included -- while `node.status`
sits below `HeaderSynced`. Measured at `btclib-node` `382a29fb`:
`submitblock` answers `None` (accepted) and stores the block, and
`getblockcount`/`getbestblockhash` never move; a second node peered to
the first over `addnode` can itself receive and connect that same block
over ordinary p2p relay, so the gap is the solo node's own status latch
and not the block or the RPC. Filed as
[ISS btclib-node#1071](https://github.com/btclib-org/btclib-node/issues/1071).

Independently,
[ISS btclib-node#1072](https://github.com/btclib-org/btclib-node/issues/1072)
is what makes `p2p_getdata` itself fail here: `block_db` never holds the
genesis block, so neither `getblock` nor a p2p `getdata` can serve the
one block a fresh regtest node -- mined or not -- starts at.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "BtclibNodeAdapter",
]

# btclib-node validates no credential at all today (measured against
# `382a29fb`: any user/password round-trips), and binds RPC to
# 127.0.0.1 only -- ISS 2135's own census, quoted in ISS 2220. A cookie
# file is bitcoind's mechanism, not this node's, so a placeholder is
# what `bitcoin_core_rpc.BitcoinCoreRpcClient` is given instead of one:
# the constructor refuses no credential at all, and this is not a secret
# guarding anything.
_RPC_USER = "tf2"
_RPC_PASSWORD = "tf2"  # noqa: S105 -- a placeholder this node never checks, not a secret


class BtclibNodeAdapter(NodeAdapter):
    """A regtest `btclib-node`, run as `python -m btclib_node`.

    Not the console script `pip install btclib-node` also provides:
    `cli.py`'s own module docstring is where the reason not to run that
    entry point directly from a spawning process is argued --
    `ReimportedMainProcessError` reaching every path but the one
    `python -m` and its own `__main__.py` exempt.
    """

    capabilities: AbstractSet[Capability] = frozenset({Capability.CONNECT})

    @override
    def _command(self) -> list[str]:
        """Return btclib-node's own argv, over `python -m btclib_node`.

        `self._executable` is the interpreter (`sys.executable` of
        whichever environment `btclib-node` is installed into), never
        the console script -- the module docstring is why.
        """
        return [
            self._executable,
            "-m",
            "btclib_node",
            "-regtest",
            f"-datadir={self._datadir}",
            f"-rpcport={self._rpc_port}",
            "-rpcbind=127.0.0.1",
            f"-port={self._p2p_port}",
        ]

    @override
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a client authenticating with a credential it never checks."""
        return BitcoinCoreRpcClient(
            f"http://127.0.0.1:{self._rpc_port}", user=_RPC_USER, password=_RPC_PASSWORD
        )
