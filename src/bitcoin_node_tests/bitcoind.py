# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`BitcoindAdapter`: the oracle, bitcoind's own regtest.

The release is `31.1`, fetched from bitcoincore.org and verified against
its published sha256, the same one
[btclib's `integration-bitcoind.yml`](https://github.com/btclib-org/btclib/blob/main/.github/workflows/integration-bitcoind.yml)
pins -- a build of `master` is a later issue of its own
([ISS 2220](https://github.com/btclib-org/btclib/issues/2220)'s step 5).
This module holds none of that fetch: it is handed the daemon's own path,
already installed, the same split
`.github/actions/install-bitcoind/action.yml` and
`tests/integration/conftest.py` keep in every tree that needs one.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

from bitcoin_core_rpc import BitcoinCoreRpcClient

from bitcoin_node_tests.capability import Capability
from bitcoin_node_tests.node import NodeAdapter

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

__all__ = [
    "BitcoindAdapter",
]


class BitcoindAdapter(NodeAdapter):
    """A regtest `bitcoind`: cookie authentication, and every capability.

    RPC authenticates by cookie, the file `-datadir` writes once the
    node is listening -- rule 1's "how RPC authenticates", answered by a
    file rather than a credential this adapter invents.

    `Capability.MINE` is `generatetoaddress` over a wallet this adapter
    creates on first use; `Capability.CONNECT` is `node.connect_nodes`
    (`node.py`), unconditional here since bitcoind answers `addnode` and
    `getnetworkinfo` the way every Core-compatible node does.
    `Capability.RAW_MESSAGE` is `sendmsgtopeer`, a debug RPC this release
    answers (measured against the pinned `31.1`: not in `help`'s own
    listing, which is for discoverability rather than availability, but
    `help sendmsgtopeer` answers its own signature) and which no other
    adapter's node offers yet. `Capability.BLK_FILES` is unconditional
    too: this is Core's own binary, so `blk*.dat` under `blocks/` is the
    format it already writes, not one this adapter has to add anything
    for. `Capability.DEBUG_LOG` is `debug_log_path` below, over the
    node's own `-debug=net`: bitcoind's own binary is what writes Core's
    own wording, which is the fact this capability names.
    `Capability.UA_COMMENT` is unconditional too: `-uacomment` is Core's
    own flag, so this is the one node under test that always has it,
    whatever a later option capability turns out to name.
    `Capability.CLOCK` is `setmocktime`, wrapped by
    `NodeAdapter.set_mock_time` (`node.py`) -- a regtest-only RPC in the
    same standing as `sendmsgtopeer` above (measured against the pinned
    `31.1`: also absent from `help`'s own listing, and also answering
    `help setmocktime` directly). `Capability.RPC_AUTH_CONFIG` is
    unconditional too: `rpcauth`, `rpcwhitelist` and
    `rpcwhitelistdefault` are this binary's own `bitcoin.conf` keys,
    read the same way regardless of which adapter wrote the file.
    `Capability.RPC_AUTH_NEGATION` is unconditional too: `-norpcauth`
    disabling every `-rpcauth` given before it is `ArgsManager`'s own
    generic negation of a list-type setting, not a fact `-rpcauth`
    itself carries -- measured live against the pinned `31.1`, a request
    authenticated with a credential named on the command line before
    `-norpcauth` gets 401 once the node has started.
    """

    capabilities: AbstractSet[Capability] = frozenset(
        {
            Capability.MINE,
            Capability.CONNECT,
            Capability.RAW_MESSAGE,
            Capability.BLK_FILES,
            Capability.DEBUG_LOG,
            Capability.UA_COMMENT,
            Capability.CLOCK,
            Capability.RPC_AUTH_CONFIG,
            Capability.RPC_AUTH_NEGATION,
        }
    )

    def __init__(
        self,
        executable: str,
        datadir: Path,
        rpc_port: int,
        p2p_port: int,
        extra_args: Sequence[str] = (),
    ) -> None:
        super().__init__(executable, datadir, rpc_port, p2p_port, extra_args)
        self._miner_wallet: str | None = None

    @override
    def _command(self) -> list[str]:
        """Return bitcoind's own argv, a loopback-only, ephemeral regtest.

        `-natpmp=0`, `-discover=0` and `-listenonion=0`: `-bind` already
        names the one address this node listens on regardless of
        `-listen`'s own default, so nothing here needs to reach a
        gateway, a public address lookup or a Tor control port -- a
        throwaway regtest node run from a test suite wants none of the
        three. `-fallbackfee` is set because a chain with no fee history
        refuses to fund a transaction without it, which `Capability.MINE`
        meets the moment a caller spends what it mines. `-debug=net` is
        `Capability.DEBUG_LOG`'s own condition: Core's own `net` category
        log lines, the ones the log family's tests read, are
        `LogDebug`'s (`src/util/log.h`) and print at all only where their
        own category is enabled -- unconditional here rather than left to
        a per-test option, `-debug` being a request no test of this
        family needs to make for itself.
        """
        return [
            self._executable,
            "-regtest",
            f"-datadir={self._datadir}",
            f"-rpcport={self._rpc_port}",
            "-rpcbind=127.0.0.1",
            f"-bind=127.0.0.1:{self._p2p_port}",
            "-natpmp=0",
            "-discover=0",
            "-listenonion=0",
            "-fallbackfee=0.0002",
            "-printtoconsole=0",
            "-debug=net",
        ]

    @override
    def _rpc_client(self) -> BitcoinCoreRpcClient:
        """Return a client authenticating by the cookie `-datadir` writes."""
        cookie_path = self._datadir / "regtest" / ".cookie"
        return BitcoinCoreRpcClient(
            f"http://127.0.0.1:{self._rpc_port}", cookie_path=cookie_path
        )

    @property
    def debug_log_path(self) -> Path:
        """Return this node's own `debug.log`, `Capability.DEBUG_LOG`'s fact.

        `-datadir`'s own `regtest/debug.log`, the same layout the cookie
        file above reads from -- bitcoind's own convention, not a name
        this adapter invents.
        """
        return self._datadir / "regtest" / "debug.log"

    def mine(self, count: int = 1) -> list[str]:
        """Mine `count` blocks to this adapter's wallet, return their hashes.

        `generatetoaddress`, over a wallet created and cached on first
        call: Core's own regtest mining needs an address to pay, and a
        fresh wallet answers `getnewaddress` with one that this same
        client can later spend from, which is `Capability.MINE`'s whole
        promise rather than only a taller chain.

        :param count: how many blocks to mine.
        :returns: the mined blocks' own hashes, Core's own
            `generatetoaddress` return value.
        """
        if self._miner_wallet is None:
            self._miner_wallet = "miner"
            self.rpc.call("createwallet", [self._miner_wallet])
        wallet_rpc = self.rpc.for_wallet(self._miner_wallet)
        address = wallet_rpc.call("getnewaddress")
        hashes = self.rpc.call("generatetoaddress", [count, address])
        if not isinstance(hashes, list):
            err_msg = f"generatetoaddress answered {hashes!r}, not a list of hashes"
            raise TypeError(err_msg)
        return hashes
