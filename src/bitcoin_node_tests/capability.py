# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""What a node can do, and how many tests skipped for lack of it.

Rule 4 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220): a
node declares its capabilities, a test needing one the node lacks skips,
and the run prints a skip count per capability -- a number the node's own
tracker can read, never a silent pass. A capability names what a node
*can do*, not how it spells the call that does it: `Capability.CONNECT`
covers what `node.connect_nodes` does today because that is the one way
both adapters answer it alike, and a node reaching it another way would
still declare the same member.

A fact that differs between two builds of one node is read from the
build under test, never fixed as a class-wide constant
([ISS bitcoin-node-tests#35](https://github.com/btclib-org/bitcoin-node-tests/issues/35)):
the class says what every build of that node can do, and the running
build says what this one can. Where the fact is whether a capability
is there at all, it is still a `Capability`, declared per *instance*
from a probe rather than fixed for the whole class:
`BtclibNodeAdapter.__init__`'s own `_writes_auth_cookie` decides, per
instance, whether `Capability.RPC_AUTH_CONFIG` is declared at all, and
`BitcoindAdapter.__init__`'s own `_has_wallet` narrows `Capability.MINE`
off an instance built against a `bitcoind` without wallet support --
`self.capabilities = type(self).capabilities - {Capability.MINE}`,
widening or narrowing the class's own frozen set rather than replacing
it outright. Where the fact is not whether a capability exists but
*how* a capability every build declares alike behaves once exercised --
whether `bitcoind`'s own `ADD_ONION` negotiates BIP434's proof-of-work
defenses (`tests/integration/feature_torcontrol_bitcoind_test.py`),
which p2p protocol version a build speaks
(`tests/integration/p2p_bip434_feature_bitcoind_test.py`) -- there is no
skip to gate, so nothing is added to this enum: the test itself reads
the fact off the running node's own RPC or its own wire behaviour and
asserts whichever shape that build produces. The enum is for what
`SkipCounts.report`'s own count is over -- an instance either declares a
member or it does not, and a run either skips a test for lacking it or
does not -- and an expectation with no skip attached to it is not that.

`p2p_getdata`, step 3's own test, needs none of the members below: it
asks only for what every adapter provides unconditionally -- a running
node, its RPC and its p2p port -- so `require` is exercised by
`tests/capability_test.py` rather than by that test. The first family's
other four tests, step 4's, are what exercises `MINE`, `CONNECT` and
`RAW_MESSAGE` each.

`UA_COMMENT` is the first of the option family
([ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3),
whose own body already answers the design question this way), and it
sets the shape every later option takes: one member per Core option a
ported test actually asks for, added the moment that test is ported
rather than declared for the whole of Core's option surface up front,
which is large and mostly untouched by any test this suite has ported.
The rejected alternative is a single parameterized `Capability.OPTION`,
keyed on the option's own name, with one node-side mapping of names to
"has it"; rule 4's own count is what this file already prints one line
per member of, sorted by value, and a parameterized capability would
need to fold that back to one line itself rather than getting it from
`SkipCounts.report` unchanged. One member per option is what keeps a
name in the enum a name in the printed summary, at the cost this module
already carries: a member added by hand, per option, per test ported. A
member's own value is what that summary prints, so it is spelled the
same as the member rather than shortened on its own, keeping the
summary's own name for a capability the same as the code's.

Not every Core option a test names earns a member here. Step 5's own
charter carries the narrower rule first: "wallet and USDT tests stay
out" and "a test of bitcoind's own options runs against bitcoind alone".
An option only bitcoind has a reason to carry -- `-disablewallet`,
`-torcontrol` -- is never declared or skipped by another node under this
mechanism; it is a bitcoind-only test's subject, a shape this module
does not build.
[ISS bitcoin-node-tests#23](https://github.com/btclib-org/bitcoin-node-tests/issues/23)
gives that shape a place of its own, and this paragraph is the one rule
that decides which option qualifies, rather than a decision made test by
test: a `*_bitcoind_test.py` module with no `*_btclib_node_test.py`
counterpart, asking `require` for nothing, is a bitcoind-only test.
`TF2.md`'s own per-test ledger spells such a row `bitcoind only` in its
`btclib-node` column rather than any `skip (...)` -- a cell nothing will
ever turn into a `pass` or a `fail`, unlike an ordinary skip.

**This module imports no test runner.** `pyproject.toml`'s own
`[project] dependencies` name two packages and no third (this
package's own `__init__.py` says so), and Core's own test framework
runs under no `pytest` at all -- objective 2 of ISS 2220 is that Core
can adopt this suite, which a hard runtime dependency on somebody
else's test runner would work against. `require` raises
`MissingCapabilityError`, its own exception, rather than calling
`pytest.skip`; `tests/conftest.py`'s own autouse fixture is what
translates that into an actual skip, in the one tree that ever runs
these tests under pytest. A prior version imported `pytest` here
directly, which `sphinx-build`'s own `autodoc` -- run from the `docs`
dependency group, which does not install `pytest` -- failed to import
with `ModuleNotFoundError: No module named 'pytest'`, cascading into
every module that imports this one.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Set as AbstractSet
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

__all__ = [
    "Capability",
    "MissingCapabilityError",
    "SkipCounts",
    "require",
]


class MissingCapabilityError(Exception):
    """Raised by `require` when the node under test does not declare it.

    Not `pytest.skip.Exception`: this module's own docstring has why.
    """


class Capability(Enum):
    """What a test may ask a node adapter for, named by what it does.

    `MINE` -- produce a block and have the node accept it as its own new
    tip, however it gets there: `generatetoaddress` for a node with a
    wallet, a client-built block over `submitblock` for one without.
    `CONNECT` -- accept a second node of its own kind as a peer, the way
    `node.connect_nodes` dials and waits for one.
    `DISCONNECT` -- drop an already-connected peer on request, the way
    `node.disconnect_nodes` asks over `disconnectnode`. Not implied by
    `CONNECT`: `addnode` and `disconnectnode` are two different RPCs, and
    a node answering the first need not answer the second (measured of
    `btclib-node`, [ISS bitcoin-node-tests#43](https://github.com/btclib-org/bitcoin-node-tests/issues/43)'s
    own finding).
    `BAN` -- record and enforce a `setban`/`listbanned`/`clearbanned` ban
    list, the way `rpc_setban`'s own subject does: an address already
    connected drops the moment it is banned. Node-linking's own third
    capability, beside `CONNECT` and `DISCONNECT`
    ([ISS bitcoin-node-tests#43](https://github.com/btclib-org/bitcoin-node-tests/issues/43)).
    `RAW_MESSAGE` -- send an arbitrary p2p message to an already-connected
    peer, named by that peer's own index, the way Core's `sendmsgtopeer`
    does on the node under test's behalf; `p2p_net_deadlock`'s own
    subject needs a node that offers it, and today only bitcoind does.
    `BLK_FILES` -- write its chain to disk the way Core does, `blk*.dat`
    files under a `blocks/` directory that a caller may read directly:
    a fact the wire has no call for, unlike where the option that names
    the directory lives, which a node without this capability may still
    accept.
    `DEBUG_LOG` -- write a debug log a caller can read and match Core's
    own wording against, the way `assert_debug_log`
    (`debug_log.py`) does. The log family (the third of step 5's five,
    [ISS 5](https://github.com/btclib-org/bitcoin-node-tests/issues/5))
    is what this names: where the fact an `assert_debug_log` call in
    Core asks about is also observable on the wire -- a disconnect,
    `getpeerinfo` -- the ported assertion reads the wire instead and
    needs no capability at all; where only the log carries it, a test
    needs this one. A node's own log is truthful about what *it* did,
    not about what Core would have called it, so a byte-for-byte match
    against Core's own wording is a fact only bitcoind's own binary can
    supply.
    `UA_COMMENT` -- append a caller-chosen comment to the subversion
    string `getnetworkinfo` reports, the fact Core's own `-uacomment`
    asks for. The first of the option family (rule 4,
    [ISS bitcoin-node-tests#3](https://github.com/btclib-org/bitcoin-node-tests/issues/3)).
    `CLOCK` -- accept a caller-set wall clock, Core's `setmocktime`
    (`test/functional/test_framework/test_node.py`'s own
    `TestNode.setmocktime`): every RPC and every p2p timeout this node
    reads the time through sees the caller's clock instead of the real
    one, until `0` is set to release it back.
    `RPC_AUTH_CONFIG` -- recognise `rpcauth`, `rpcwhitelist` and
    `rpcwhitelistdefault` written into `bitcoin.conf`, the way Core's
    own `rpc_users` and `rpc_whitelist` add a credential or restrict its
    RPC surface through the config file rather than the command line.
    The disk family's own second capability
    ([ISS bitcoin-node-tests#7](https://github.com/btclib-org/bitcoin-node-tests/issues/7)):
    the fact is `bitcoin.conf` itself, `datadir_path`'s own file, not a
    fact the wire has a call for.
    `RPC_AUTH_NEGATION` -- recognise `-norpcauth` on the command line,
    disabling every `-rpcauth` value given before it, the way Core's own
    `rpc_users` checks it. Not `RPC_AUTH_CONFIG` itself: a node can parse
    `-rpcauth` and still have no `-no<name>` negation of any kind, which
    is `btclib-node`'s own case
    ([ISS btclib-node#1176](https://github.com/btclib-org/btclib-node/issues/1176)),
    so a test asking for the negation needs its own capability rather
    than riding on the one for the value it negates.
    `TEST_ACTIVATION_HEIGHT` -- hold one buried soft fork's own deployment
    inactive until a caller-chosen height, Core's own debug-only
    `-testactivationheight=<deployment>@<height>`. Regtest's own chain
    parameters activate every buried deployment -- BIP34, BIP66, BIP65,
    CSV -- from height 1 otherwise (`src/kernel/chainparams.cpp`'s
    own comment on each, "Always active unless overridden", measured
    against the pinned `31.1`), so this is what lets a test hold one of
    them back long enough to observe the boundary at all
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)).
    `V2TRANSPORT` -- accept BIP324 v2 connections *from another node of
    this kind*, the way Core's own `-v2transport` does: `getpeerinfo`'s
    `transport_protocol_type` reads `v2` on such a connection. Not a fact
    about a `Peer` (`peer.py`): that class speaks only the plaintext v1
    wire format, so this capability is unconditional on node-to-node
    connections alone -- issue
    [bitcoin-node-tests#36](https://github.com/btclib-org/bitcoin-node-tests/issues/36).
    `DATACARRIER` -- recognise `-datacarrier` and `-datacarriersize`,
    Core's own pair of relay-policy knobs for an `OP_RETURN` output: the
    first turns its relay on or off, the second bounds how large one may
    be. One member for the pair rather than two: neither flag is ever
    tested apart from the other in
    [ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
    own `mempool_datacarrier.py`, both landing at once.
    `PERMIT_BARE_MULTISIG` -- recognise `-permitbaremultisig`, Core's own
    switch for whether a bare `OP_CHECKMULTISIG` output is relayed at
    all, checked apart from `DUST_RELAY_FEE` because a test can ask for
    either alone.
    `DUST_RELAY_FEE` -- recognise `-dustrelayfee`, Core's own per-kilobyte
    rate an output's own value is measured against to call it dust.
    `BYTES_PER_SIGOP` -- recognise `-bytespersigop`, Core's own
    conversion rate from a sigop to the virtual bytes a transaction's own
    mempool footprint is billed for.
    `LIMIT_CLUSTER_COUNT` -- recognise `-limitclustercount`, Core's own
    cap on how many transactions, in-mempool and in-package together, one
    mempool cluster may hold
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
    own `mempool_package_limits.py`). Checked apart from
    `LIMIT_CLUSTER_SIZE`: a test can ask for either alone, and each
    ported file so far does.
    `LIMIT_CLUSTER_SIZE` -- recognise `-limitclustersize`, Core's own cap
    on one cluster's own total virtual size
    (`mempool_updatefromblock.py`).
    `DESCRIPTOR_ACTIVITY` -- answer `getdescriptoractivity`, Core's own
    RPC pairing spend and receive events with the descriptors and blocks
    a caller names. Named for the RPC rather than for an option, the way
    `MINE`/`CONNECT`/`DISCONNECT`/`BAN`/`RAW_MESSAGE` already are: no
    flag gates it, so what a node either answers or does not is the
    method itself
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)).
    `BLOCK_STATS` -- answer `getblockstats`, Core's own per-block
    statistics RPC, named the same way and for the same reason.
    `FASTPRUNE` -- recognise `-fastprune`, Core's own debug-only switch
    to block files far smaller than a real node's, so that a test reaches
    a block file's size limit with a single large block
    ([ISS bitcoin-node-tests#14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s
    own `feature_fastprune.py`).
    `INBOUND_EVICTION` -- make room for a new inbound peer, once its
    inbound slots are full, by disconnecting an existing one that none of
    Core's own protections covers, the slots being what `-maxconnections`
    bounds (`p2p_eviction.py`). Named for the eviction rather than for
    the option: a node can accept `-maxconnections` and refuse the new
    peer instead of evicting an old one.
    `BLOCK_FILTER_INDEX` -- keep BIP158's basic block filter for every
    block once `-blockfilterindex` asks for it, and answer `scanblocks`
    from that index (`rpc_scanblocks.py`).
    """

    MINE = "mine"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    BAN = "ban"
    RAW_MESSAGE = "raw_message"
    BLK_FILES = "blk_files"
    DEBUG_LOG = "debug_log"
    UA_COMMENT = "ua_comment"
    CLOCK = "clock"
    RPC_AUTH_CONFIG = "rpc_auth_config"
    RPC_AUTH_NEGATION = "rpc_auth_negation"
    TEST_ACTIVATION_HEIGHT = "test_activation_height"
    V2TRANSPORT = "v2transport"
    DATACARRIER = "datacarrier"
    PERMIT_BARE_MULTISIG = "permit_bare_multisig"
    DUST_RELAY_FEE = "dust_relay_fee"
    BYTES_PER_SIGOP = "bytes_per_sigop"
    LIMIT_CLUSTER_COUNT = "limit_cluster_count"
    LIMIT_CLUSTER_SIZE = "limit_cluster_size"
    DESCRIPTOR_ACTIVITY = "descriptor_activity"
    BLOCK_STATS = "block_stats"
    FASTPRUNE = "fastprune"
    INBOUND_EVICTION = "inbound_eviction"
    BLOCK_FILTER_INDEX = "block_filter_index"


class SkipCounts:
    """One session's own tally of skips, one count per capability asked for.

    Session-scoped in `tests/integration/conftest.py`, so that one run
    against however many nodes prints one total per capability rather
    than one line per test -- the number rule 4 asks for is a count the
    node's tracker can read, not a running commentary.
    """

    def __init__(self) -> None:
        self._counts: Counter[Capability] = Counter()

    def record(self, capability: Capability) -> None:
        """Count one more skip against `capability`."""
        self._counts[capability] += 1

    def __iter__(self) -> Iterator[tuple[Capability, int]]:
        """Yield `(capability, count)` for every capability ever recorded.

        Sorted by the capability's own value, so the report below reads
        the same from one run to the next rather than in whatever order
        a `Counter` happens to have built up.
        """
        yield from sorted(self._counts.items(), key=lambda pair: pair[0].value)

    def report(self) -> str:
        """Return one line per capability recorded, or say that none was."""
        lines = [f"{capability.value}: {count}" for capability, count in self]
        if not lines:
            return "skips per capability: no test asked for one this run"
        return "skips per capability:\n" + "\n".join(lines)

    def as_mapping(self) -> dict[str, int]:
        """Return this tally as a plain `{capability.value: count}` mapping.

        `tests/integration/conftest.py` is what this is for: an xdist
        worker's own tally has to cross to the controller through
        `workeroutput`, and the channel that carries it serializes plain
        data, never an `Enum` member -- `add_mapping` is this method's
        own inverse, on the controller's own tally.
        """
        return {capability.value: count for capability, count in self}

    def add_mapping(self, mapping: Mapping[str, int]) -> None:
        """Add counts from another tally's own `as_mapping` into this one.

        :param mapping: a `{capability.value: count}` mapping, as
            `as_mapping` returns.
        """
        for value, count in mapping.items():
            self._counts[Capability(value)] += count


def require(
    capability: Capability, capabilities: AbstractSet[Capability], counts: SkipCounts
) -> None:
    """Raise `MissingCapabilityError` unless `capability` is in `capabilities`.

    :param capability: what the test about to run needs.
    :param capabilities: what the node under test declares, an adapter's
        own `capabilities`.
    :param counts: the session's own tally, credited before the raise so
        that a node lacking a capability still has that asked for it
        counted -- rule 4's "never a silent pass" reaching the count
        itself, not only the individual test.
    :raises MissingCapabilityError: where `capability` is missing.
    """
    if capability not in capabilities:
        counts.record(capability)
        msg = f"node does not declare {capability.value}"
        raise MissingCapabilityError(msg)
