# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""How every default wait in `node.py`, `peer.py`, `debug_log.py` is scaled.

Core's own `--timeout-factor` (`test_framework.py`) multiplies every
`wait_until` call by one value read off a `TestFramework` instance; this
package spawns no such object for a value like that to live on, so a
small mutable singleton serves in its place -- set once per process by
`tests/integration/conftest.py`'s own `--timeout-factor` option, before
any node starts. Under `-n auto` this module loads once per xdist worker
and once in the controller, each with its own `_factor`; every worker
receives the same command line, so every process scales the same way,
matching the "one tally per process" scope `tests/integration/conftest.py`'s
own `SkipCounts` already carries for the identical reason.
"""

from __future__ import annotations

__all__ = [
    "scaled",
    "set_factor",
]


class _Factor:
    """This process's own multiplier, mutable so `set_factor` can update it."""

    value: float = 1.0


_factor = _Factor()


def set_factor(factor: float) -> None:
    """Set the multiplier `scaled` applies from now on, in this process.

    :param factor: what `--timeout-factor` asks for; `1.0` leaves every
        wait exactly as written, matching Core's own default.
    """
    _factor.value = factor


def scaled(seconds: float) -> float:
    """Return `seconds`, multiplied by whatever `set_factor` last set.

    :param seconds: a wait this package would otherwise use unscaled.
    """
    return seconds * _factor.value
