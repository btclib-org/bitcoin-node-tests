# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `feature_uacomment`, one body over each node.

Read from Core's `test/functional/feature_uacomment.py` (`fa5f29774872`,
2025-12-16) and ported in part, the first test of the option family
(rule 4 of issue btclib-org/btclib#2220,
[ISS btclib-functional-tests#3](https://github.com/btclib-org/btclib-functional-tests/issues/3)):
`-uacomment` appends a comment to the subversion string
`getnetworkinfo` reports. No other step-5 mechanism is asked for, nor
`Capability.MINE` nor an outbound connection.

A smaller claim than Core's own test, declared rather than silent:
Core's own harness sets `-uacomment=testnode{i}` on every node it
starts and asserts a second comment is appended alongside that one on
restart; this adapter sets no default comment, so the claim kept is
that one appears once named, on a restart of a node carrying none,
rather than that a second one joins a first. The length-limit and
unsafe-character checks are dropped too: both ask a node to refuse to
start on a bad value, which is a fact about a rejected argument, not
about this capability.

Each `feature_uacomment_<node>_test.py` module beside this one runs it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from btclib_functional_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from btclib_functional_tests.capability import SkipCounts
    from btclib_functional_tests.node import NodeAdapter

__all__ = ["uacomment_appends_to_the_subversion_string"]


def uacomment_appends_to_the_subversion_string(
    cluster: Callable[[int], Sequence[NodeAdapter]],
    skip_counts: SkipCounts,
) -> None:
    """Check a comment appears in `getnetworkinfo`'s subversion once named.

    :param cluster: a node's own cluster fixture.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.UA_COMMENT, node.capabilities, skip_counts)
    assert "(" not in node.rpc.call("getnetworkinfo")["subversion"]

    node.restart(["-uacomment=foo"])
    assert "(foo)" in node.rpc.call("getnetworkinfo")["subversion"]
