# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `rpc_getdescriptorinfo`, rewritten on this harness: bitcoind.

Read from Core's `test/functional/rpc_getdescriptorinfo.py`
(`fa5f29774872`, 2025-12-16). Its subject is `getdescriptorinfo`: every
descriptor of `DESCRIPTORS` answers the same whether it is asked with
its checksum or without, and answers its own checksummed form -- or,
where it is multipath, the first of the single-path descriptors its row
names, with all of them as `multipath_expansion` -- together with the
`isrange`, `issolvable` and `hasprivatekeys` its row names. A missing
argument, an argument of the wrong type, an empty descriptor and a key
with whitespace beside it are each refused with Core's own code and
message. `Capability.DESCRIPTOR_INFO` gates each test.

Every descriptor, flag and message of `DESCRIPTORS` and
`WHITESPACE_KEYS` is Core's own, copied from that file at that revision
in its own order. That file is "Copyright (c) 2019-present The Bitcoin
Core developers", distributed under the MIT software license.

Where this differs from Core's own file:

- Core's own node starts with `-disablewallet`, an option
  `capability.py`'s module docstring names as only bitcoind's to carry;
  this module asks the session's shared `bitcoind_adapter`, which passes
  no such option. `getdescriptorinfo` is registered in
  `src/rpc/output_script.cpp`, not among the wallet's RPCs.
- A checksum is btclib's: `descriptors.add_checksum` computes each
  expected checksummed form where Core's own `descsum_create`
  (`test_framework/descriptors.py`) does, and the node's own answer is
  compared with it.
- The private key refused for whitespace is a random regtest WIF built
  with btclib's `b58.wif_from_prv_key`, where Core's own is
  `wallet_util.generate_keypair(wif=True)`'s.
- The wrong-type refusal is always asked: Core's own file skips it under
  `--usecli`, an option this harness has no counterpart for.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest
from bitcoin_core_rpc import RpcError
from btclib.b58 import wif_from_prv_key
from btclib.curves import secp256k1
from btclib.descriptors.descriptors import add_checksum

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from bitcoin_node_tests.capability import SkipCounts

pytestmark = pytest.mark.integration

# each row a descriptor, whether it is ranged, solvable and carries a
# private key, and the single-path descriptors a multipath one expands to
DESCRIPTORS: list[tuple[str, bool, bool, bool, list[str] | None]] = [
    # P2PK output with the specified public key.
    (
        "pk(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)",
        False,
        True,
        False,
        None,
    ),
    # P2PKH output with the specified public key.
    (
        "pkh(02c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5)",
        False,
        True,
        False,
        None,
    ),
    # P2WPKH output with the specified public key.
    (
        "wpkh(02f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9)",
        False,
        True,
        False,
        None,
    ),
    # P2SH-P2WPKH output with the specified public key.
    (
        "sh(wpkh(03fff97bd5755eeea420453a14355235d382f6472f8568a18b2f057a1460297556))",
        False,
        True,
        False,
        None,
    ),
    # Any P2PK, P2PKH, P2WPKH, or P2SH-P2WPKH output with the specified public
    # key.
    (
        "combo(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)",
        False,
        True,
        False,
        None,
    ),
    # An (overly complicated) P2SH-P2WSH-P2PKH output with the specified public
    # key.
    (
        "sh(wsh(pkh(02e493dbf1c10d80f3581e4904930b1404cc6c13900ee0758474fa94abe8c4cd13)))",
        False,
        True,
        False,
        None,
    ),
    # A bare *1-of-2* multisig output with keys in the specified order.
    (
        "multi(1,022f8bde4d1a07209355b4a7250a5c5128e88b84bddc619ab7cba8d569b240efe4,025cbdf0646e5db4eaa398f365f2ea7a0e3d419b7e0330e39ce92bddedcac4f9bc)",
        False,
        True,
        False,
        None,
    ),
    # A P2SH *2-of-2* multisig output with keys in the specified order.
    (
        "sh(multi(2,022f01e5e15cca351daff3843fb70f3c2f0a1bdd05e5af888a67784ef3e10a2a01,03acd484e2f0c7f65309ad178a9f559abde09796974c57e714c35f110dfc27ccbe))",
        False,
        True,
        False,
        None,
    ),
    # A P2WSH *2-of-3* multisig output with keys in the specified order.
    (
        "wsh(multi(2,03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7,03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb,03d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a))",
        False,
        True,
        False,
        None,
    ),
    # A P2SH-P2WSH *1-of-3* multisig output with keys in the specified order.
    (
        "sh(wsh(multi(1,03f28773c2d975288bc7d1d205c3748651b075fbc6610e58cddeeddf8f19405aa8,03499fdf9e895e719cfd64e67f07d38e3226aa7b63678949e6e49b241a60e823e4,02d7924d4f7d43ea965a465ae3095ff41131e5946f3c85f79e44adbcf8e27e080e)))",
        False,
        True,
        False,
        None,
    ),
    # A P2PK output with the public key of the specified xpub.
    (
        "pk(tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B)",
        False,
        True,
        False,
        None,
    ),
    # A P2PKH output with child key *1'/2* of the specified xpub.
    (
        "pkh(tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/1h/2)",
        False,
        True,
        False,
        None,
    ),
    # A set of P2PKH outputs, but additionally specifies that the specified
    # xpub is a child of a master with fingerprint `d34db33f`, and derived
    # using path `44'/0'/0'`.
    (
        "pkh([d34db33f/44h/0h/0h]tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/1/*)",
        True,
        True,
        False,
        None,
    ),
    # A set of *1-of-2* P2WSH multisig outputs where the first multisig key is
    # the *1/0/`i`* child of the first specified xpub and the second multisig
    # key is the *0/0/`i`* child of the second specified xpub, and `i` is any
    # number in a configurable range (`0-1000` by default).
    (
        "wsh(multi(1,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/1/0/*,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/0/0/*))",
        True,
        True,
        False,
        None,
    ),
    # A multipath descriptor
    (
        "wpkh(tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/<0;1>/*)",
        True,
        True,
        False,
        [
            "wpkh(tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/0/*)",
            "wpkh(tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/1/*)",
        ],
    ),
    (
        "wsh(multi(1,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/<1;2>/0/*,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/<2;3>/0/*))",
        True,
        True,
        False,
        [
            "wsh(multi(1,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/1/0/*,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/2/0/*))",
            "wsh(multi(1,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/2/0/*,tpubD6NzVbkrYhZ4WaWSyoBvQwbpLkojyoTZPRsgXELWz3Popb3qkjcJyJUGLnL4qHHoQvao8ESaAstxYSnhyswJ76uZPStJRJCTKvosUCJZL5B/3/0/*))",
        ],
    ),
]

# each row a descriptor with whitespace beside one of its keys, and the
# refusal that names the key
WHITESPACE_KEYS: list[tuple[str, str]] = [
    (
        "pk( 0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798)",
        "pk(): Key ' 0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798' is invalid due to whitespace",
    ),
    (
        "pk(0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798 )",
        "pk(): Key '0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798 ' is invalid due to whitespace",
    ),
    (
        "wsh(multi(2, 03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7,03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb,03d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a))",
        "Multi: Key ' 03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7' is invalid due to whitespace",
    ),
    (
        "wsh(multi(2,03a0434d9e47f3c86235477c7b1ae6ae5d3442d49b1943c2b752a68e2a47e247c7, 03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb,03d01115d548e7561b15c38f004d734633687cf4419620095bc5b0f47070afe85a))",
        "Multi: Key ' 03774ae7f858a9411e5ef4246b70c65aac5649980be5c17891bbec17895da008cb' is invalid due to whitespace",
    ),
]


def _refusal(node: BitcoindAdapter, *params: object) -> tuple[int, str]:
    """Return the code and message `getdescriptorinfo` refuses `params` with."""
    with pytest.raises(RpcError) as excinfo:
        node.rpc.call("getdescriptorinfo", list(params))
    return excinfo.value.code, str(excinfo.value)


def test_malformed_requests_are_refused(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """A missing, mistyped, empty or whitespace-padded argument is refused."""
    require(Capability.DESCRIPTOR_INFO, bitcoind_adapter.capabilities, skip_counts)
    node = bitcoind_adapter

    # a missing argument earns the RPC's own help, which opens with its name
    code, message = _refusal(node)
    assert code == -1
    assert "getdescriptorinfo" in message

    code, message = _refusal(node, 1)
    assert code == -3
    assert "JSON value of type number is not of expected type string" in message

    code, message = _refusal(node, "")
    assert code == -5
    assert "'' is not a valid descriptor function" in message

    prv_key = wif_from_prv_key(secrets.randbelow(secp256k1.n - 1) + 1, "regtest")
    whitespace_keys = [
        *WHITESPACE_KEYS,
        (f"pk( {prv_key})", f"pk(): Key ' {prv_key}' is invalid due to whitespace"),
    ]
    for descriptor, expected in whitespace_keys:
        code, message = _refusal(node, descriptor)
        assert code == -5
        assert expected in message, descriptor


def test_descriptors_answer_their_info(
    bitcoind_adapter: BitcoindAdapter, skip_counts: SkipCounts
) -> None:
    """Each of `DESCRIPTORS` answers its checksummed form and its flags."""
    require(Capability.DESCRIPTOR_INFO, bitcoind_adapter.capabilities, skip_counts)
    node = bitcoind_adapter
    for descriptor, isrange, issolvable, hasprivatekeys, expanded in DESCRIPTORS:
        info = node.rpc.call("getdescriptorinfo", [descriptor])
        assert info == node.rpc.call("getdescriptorinfo", [add_checksum(descriptor)]), (
            descriptor
        )
        if expanded is None:
            assert info["descriptor"] == add_checksum(descriptor)
            assert "multipath_expansion" not in info, descriptor
        else:
            assert info["descriptor"] == add_checksum(expanded[0])
            assert info["multipath_expansion"] == [add_checksum(d) for d in expanded]
        assert (info["isrange"], info["issolvable"], info["hasprivatekeys"]) == (
            isrange,
            issolvable,
            hasprivatekeys,
        ), descriptor
