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
    """

    MINE = "mine"
    CONNECT = "connect"
    RAW_MESSAGE = "raw_message"
    BLK_FILES = "blk_files"
    DEBUG_LOG = "debug_log"
    UA_COMMENT = "ua_comment"
    CLOCK = "clock"
    RPC_AUTH_CONFIG = "rpc_auth_config"


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
