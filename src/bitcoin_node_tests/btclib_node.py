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

`Capability.BLK_FILES` is not declared either, and is not a gap this
adapter is waiting on: `block_db.BlockDB` is its own on-disk format, not
Core's `blk*.dat`, by the decision
[ISS btclib-node#573](https://github.com/btclib-org/btclib-node/issues/573)
already made and closed on -- reading Core's own files was refused in
favour of `-connect`/`-addnode` delivering the same blocks over loopback
p2p, which this repository's own `Capability.CONNECT` already reaches.

`Capability.UA_COMMENT` is not declared: measured against `cli.py`'s
own `_build_parser` at `btclib-node` `18b6ae1e`, `-uacomment` is not
one of its registered flags.

`Capability.CLOCK` is not declared: `setmocktime` names no callback in
`src/btclib_node/rpc/callbacks.py`'s own dispatch table, measured at
`btclib-node` `18b6ae1e2c74`.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "BtclibNodeAdapter",
]

# btclib-node's own build before ISS btclib-node#1070 (`382a29fb`, still
# what PyPI's `2026.9.24` release installs) checks no credential at all
# and binds RPC to 127.0.0.1 only -- ISS 2135's own census, quoted in ISS
# 2220 -- so a placeholder is what `bitcoin_core_rpc.BitcoinCoreRpcClient`
# is given for that build instead of one the constructor refuses to be
# built with none of: `_writes_auth_cookie` below is what decides whether
# it is used at all, rather than the cookie every later build writes.
_RPC_USER = "tf2"
_RPC_PASSWORD = "tf2"  # noqa: S105 -- ignored by a pre-#1070 build; see above


@lru_cache
def _writes_auth_cookie(executable: str) -> bool:
    """Return whether `executable`'s own btclib-node writes an RPC cookie.

    ISS btclib-node#1070 (`18b6ae1e`) landed Core-style RPC authentication
    -- `-rpcuser`/`-rpcpassword`, the cookie `rpc/auth.py`'s own
    `RpcAuth.start` writes to `<data_dir>/regtest/.cookie` unless one of
    them is given, and `-rpcwhitelist` -- and gained the module
    `btclib_node.rpc.auth` along with it, absent from every build before.
    Its presence is what this checks, matching the probe
    `tests/integration/conftest.py`'s own `btclib_node_python` fixture
    already makes for the package itself. A build before it (`382a29fb`)
    checks no credential at all and answers unrecognised any
    `-rpcuser`/`-rpcpassword` given on its own argv -- confirmed live,
    exit `2` there before the node's RPC ever starts.

    A probe of the interpreter/version pair, never of a running node: no
    port is bound and no data directory is created. Cached per
    `executable`, because the answer is a fact about the install rather
    than about any one adapter instance, and `_rpc_client` below is
    called fresh on every access to `.rpc`.

    :param executable: the interpreter `btclib-node` is installed into.
    """
    probe = subprocess.run(  # noqa: S603
        [executable, "-c", "import btclib_node.rpc.auth"],
        check=False,
        capture_output=True,
    )
    return probe.returncode == 0


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
        the console script -- the module docstring is why. Carries no
        `-rpcuser`/`-rpcpassword`: a build before ISS btclib-node#1070
        refuses either flag outright, so the credential is `_rpc_client`
        below's alone, never this argv's.
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
        """Return a client authenticating the way this build actually checks.

        Cookie authentication, `BitcoindAdapter`'s own mechanism, where
        `_writes_auth_cookie` finds the build writes one -- the same
        `<datadir>/regtest/.cookie` layout, `chains.RegTest`'s own `name`
        matching bitcoind's `regtest` subdirectory. A build with no
        Core-style RPC authentication at all is given the placeholder
        credential instead, which it never checks.
        """
        url = f"http://127.0.0.1:{self._rpc_port}"
        if _writes_auth_cookie(self._executable):
            return BitcoinCoreRpcClient(
                url, cookie_path=self._datadir / "regtest" / ".cookie"
            )
        return BitcoinCoreRpcClient(url, user=_RPC_USER, password=_RPC_PASSWORD)
