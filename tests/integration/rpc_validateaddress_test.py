# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_validateaddress`, one body over either node.

Read from Core's `test/functional/rpc_validateaddress.py` (`fa5f29774872`,
2025-12-16). Its subject is `validateaddress` on the main chain, where a
`bc1` address is one of this chain's own and a `tb1` or `tc1` one is
not: every address of `INVALID_DATA` answers `isvalid` false with the
error and the `error_locations` its row names, and every address of
`VALID_DATA` answers `isvalid` true with the `scriptPubKey` its row
names and neither the error nor its locations. `NodeAdapter`'s own
`chain="main"` (`node.py`) is what starts the node there
([ISS 63](https://github.com/btclib-org/bitcoin-node-tests/issues/63)),
under Core's own `-prune=899`. `Capability.VALIDATE_ADDRESS` gates each
test.

`INVALID_DATA` and `VALID_DATA` are Core's own, copied from that file at
that revision row for row, duplicates included; `VALID_DATA`'s
commented-out `tb1` rows are left out, being no data.
That file is "Copyright (c) 2023-present The Bitcoin Core developers",
distributed under the MIT software license.

Core's own claim in full: each address is asked once, as Core's own
loop asks it, and the answers of a table are compared together. One
assertion is added, that `getblockchaininfo` answers `main` before any
address is asked.

Each test builds its node over a data directory of its own, through
`make_adapter` (`tests/integration/conftest.py`), since it starts the
node on the main chain.
`rpc_validateaddress_bitcoind_test.py` and
`rpc_validateaddress_btclib_node_test.py` run it,
`tests/integration/conftest.py`'s own module docstring having how.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from bitcoin_node_tests.capability import Capability, require
from bitcoin_node_tests.node import free_ports

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bitcoin_node_tests.bitcoind import BitcoindAdapter
    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts
    from tests.conftest import AdapterFactory

__all__ = [
    "INVALID_DATA",
    "VALID_DATA",
    "invalid_addresses_answer_their_error",
    "valid_addresses_answer_their_script_pub_key",
]

# each row an address, the error it earns and that error's locations
INVALID_DATA: list[tuple[str, str, list[int]]] = [
    # BIP 173
    (
        "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",
        # Invalid hrp
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    ("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5", "Invalid Bech32 checksum", [41]),
    (
        "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "bc1rw5uspcuh",
        # Invalid program length
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90",
        # Invalid program length
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
        "Invalid Bech32 v0 address program size (16 bytes), per BIP141",
        [],
    ),
    (
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7",
        # tb1, Mixed case
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3t4",
        # bc1, Mixed case, not in BIP 173 test vectors
        "Invalid character or mixed case",
        [40],
    ),
    (
        "bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du",
        # Wrong padding
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv",
        # tb1, Non-zero padding in 8-to-5 conversion
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    ("bc1gmk9yu", "Empty Bech32 data section", []),
    # BIP 350
    (
        "tc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq5zuyut",
        # Invalid human-readable part
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    (
        "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd",
        # Invalid checksum (Bech32 instead of Bech32m)
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "tb1z0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqglt7rf",
        # tb1, Invalid checksum (Bech32 instead of Bech32m)
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    (
        "BC1S0XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ54WELL",
        # Invalid checksum (Bech32 instead of Bech32m)
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh",
        # Invalid checksum (Bech32m instead of Bech32)
        "Version 0 witness address must use Bech32 checksum",
        [],
    ),
    (
        "tb1q0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq24jc47",
        # tb1, Invalid checksum (Bech32m instead of Bech32)
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    (
        "bc1p38j9r5y49hruaue7wxjce0updqjuyyx0kh56v8s25huc6995vvpql3jow4",
        # Invalid character in checksum
        "Invalid Base 32 character",
        [59],
    ),
    (
        "BC130XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ7ZWS8R",
        "Invalid Bech32 address witness version",
        [],
    ),
    ("bc1pw5dgrnzv", "Invalid Bech32 address program size (1 byte)", []),
    (
        "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v8n0nx0muaewav253zgeav",
        "Invalid Bech32 address program size (41 bytes)",
        [],
    ),
    (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
        "Invalid Bech32 v0 address program size (16 bytes), per BIP141",
        [],
    ),
    (
        "tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq47Zagq",
        # tb1, Mixed case
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    (
        "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v07qwwzcrf",
        # zero padding of more than 4 bits
        "Invalid padding in Bech32 data section",
        [],
    ),
    (
        "tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4j",
        # tb1, Non-zero padding in 8-to-5 conversion
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",
        [],
    ),
    ("bc1gmk9yu", "Empty Bech32 data section", []),
]

# each row an address and the scriptPubKey it decodes to, as hex
VALID_DATA: list[tuple[str, str]] = [
    # BIP 350
    (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",
        "0014751e76e8199196d454941c45d1b3a323f1433bd6",
    ),
    (
        "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3",
        "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",
    ),
    (
        "bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kt5nd6y",
        "5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6",
    ),
    ("BC1SW50QGDZ25J", "6002751e"),
    ("bc1zw508d6qejxtdg4y5r3zarvaryvaxxpcs", "5210751e76e8199196d454941c45d1b3a323"),
    (
        "bc1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvses5wp4dt",
        "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ),
    (
        "bc1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvses7epu4h",
        "5120000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ),
    (
        "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0",
        "512079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
    ),
    # PayToAnchor, P2A
    ("bc1pfeessrawgf", "51024e73"),
]


@contextmanager
def _main_node(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> Iterator[BitcoindAdapter | BtclibNodeAdapter]:
    """Yield a node started on the main chain, as Core's test starts one.

    `Capability.VALIDATE_ADDRESS` is asked of the node before it starts.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: the node's own data directory.
    :param skip_counts: the session's own tally.
    """
    rpc_port, p2p_port = free_ports(2)
    adapter = make_adapter(
        cls,
        executable,
        tmp_path,
        rpc_port,
        p2p_port,
        extra_args=("-prune=899",),
        chain="main",
    )
    require(Capability.VALIDATE_ADDRESS, adapter.capabilities, skip_counts)
    adapter.start()
    try:
        assert adapter.rpc.call("getblockchaininfo")["chain"] == "main"
        yield adapter
    finally:
        adapter.stop()


def invalid_addresses_answer_their_error(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check each of `INVALID_DATA` is refused with its own error and locations.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: the node's own data directory.
    :param skip_counts: the session's own tally.
    """
    with _main_node(make_adapter, cls, executable, tmp_path, skip_counts) as node:
        answers = []
        for address, _, _ in INVALID_DATA:
            info = node.rpc.call("validateaddress", [address])
            answers.append(
                (address, info["isvalid"], info["error"], info["error_locations"])
            )
    expected = [
        (address, False, error, locations) for address, error, locations in INVALID_DATA
    ]
    assert answers == expected


def valid_addresses_answer_their_script_pub_key(
    make_adapter: AdapterFactory,
    cls: type[BitcoindAdapter | BtclibNodeAdapter],
    executable: str,
    tmp_path: Path,
    skip_counts: SkipCounts,
) -> None:
    """Check each of `VALID_DATA` decodes to its `scriptPubKey`, and no error.

    :param make_adapter: the session's own adapter factory.
    :param cls: `BitcoindAdapter` or `BtclibNodeAdapter`.
    :param executable: the node's binary, or the interpreter running it.
    :param tmp_path: the node's own data directory.
    :param skip_counts: the session's own tally.
    """
    with _main_node(make_adapter, cls, executable, tmp_path, skip_counts) as node:
        answers = []
        for address, _ in VALID_DATA:
            info = node.rpc.call("validateaddress", [address])
            answers.append(
                (
                    address,
                    info["isvalid"],
                    info["scriptPubKey"],
                    "error" in info,
                    "error_locations" in info,
                )
            )
    expected = [
        (address, True, script_pub_key, False, False)
        for address, script_pub_key in VALID_DATA
    ]
    assert answers == expected
