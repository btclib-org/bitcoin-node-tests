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
    from collections.abc import Iterator

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
    """

    MINE = "mine"
    CONNECT = "connect"
    RAW_MESSAGE = "raw_message"


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
