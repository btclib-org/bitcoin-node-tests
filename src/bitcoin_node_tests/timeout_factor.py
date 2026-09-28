# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""How every default wait and the adapters' RPC client timeout are scaled.

Core's own `--timeout-factor` (`test_framework.py`) multiplies every
`wait_until` call by one value read off a `BitcoinTestFramework`
instance; this package spawns no such object for a value like that to
live on, so a small mutable singleton serves in its place -- set once per
process by `tests/integration/conftest.py`'s own `--timeout-factor`
option, before any node starts. Under `-n auto` this module loads once
per xdist worker and once in the controller, each with its own
`_factor`; every worker receives the same command line, so every process
scales the same way, matching the "one tally per process" scope
`tests/integration/conftest.py`'s own `SkipCounts` already carries for
the identical reason.
"""

from __future__ import annotations

__all__ = [
    "factor_from_option",
    "rpc_client_timeout",
    "scaled",
    "set_factor",
]

# Core's own `BitcoinTestFramework.rpc_timeout` (`test_framework.py`), before
# `--timeout-factor` scales it
_RPC_TIMEOUT = 60

# what Core's own `BitcoinTestFramework.parse_args` (`test_framework.py`) puts
# in place of a `--timeout-factor` of 0
_NO_TIMEOUT_FACTOR = 999


class _Factor:
    """This process's own multiplier, mutable so `set_factor` can update it."""

    value: float = 1.0


_factor = _Factor()


def factor_from_option(value: str) -> float:
    """Return the multiplier `--timeout-factor value` asks for.

    Core's own reading of the option: its help says "Setting it to 0
    disables all timeouts", and `BitcoinTestFramework.parse_args`
    (`test_framework.py`) does that by putting 999 in place of 0, so
    every wait is still a bound, only a very long one. Any other value,
    a negative one included, is kept as given, as Core keeps it.

    :param value: the option's own text, as the command line gives it.
    :raises ValueError: `value` is not a number.
    """
    factor = float(value)
    return _NO_TIMEOUT_FACTOR if factor == 0 else factor


def set_factor(factor: float) -> None:
    """Set the multiplier `scaled` applies from now on, in this process.

    :param factor: the multiplier itself, taken as given:
        `--timeout-factor` reaches it through `factor_from_option`, so a
        0 here is the caller's own and makes every wait 0. `1.0` leaves
        every wait exactly as written, matching Core's own default.
    """
    _factor.value = factor


def scaled(seconds: float) -> float:
    """Return `seconds`, multiplied by whatever `set_factor` last set.

    :param seconds: a wait this package would otherwise use unscaled.
    """
    return seconds * _factor.value


def rpc_client_timeout() -> int:
    """Return the seconds an adapter's RPC client may hold one call.

    Core's own bound, scaled the same way: `BitcoinTestFramework.__init__`
    sets `rpc_timeout` to 60 and then to
    `int(self.rpc_timeout * self.options.timeout_factor)`
    (`test_framework.py`), and `TestNode.create_new_rpc_connection` gives a
    connection whose caller names no `client_timeout` `rpc_timeout // 2`,
    "to allow for one retry in case of ETIMEDOUT" (`test_node.py`) -- 30 at
    the default factor. A factor below 1/30 makes it 0, which
    `bitcoin_core_rpc.BitcoinCoreRpcClient` refuses to be built with.
    """
    return int(scaled(_RPC_TIMEOUT)) // 2
