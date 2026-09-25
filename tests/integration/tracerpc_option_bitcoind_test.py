# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `--tracerpc`, restated as a pytest option: bitcoind, over a real RPC.

Issue [bitcoin-node-tests#36](https://github.com/btclib-org/bitcoin-node-tests/issues/36):
`tests/node_test.py`'s own tests prove `node.traced_transport` in
isolation, a fake transport standing in for the real one; this is the
same wrapper reaching an actual node's own RPC, `BitcoindAdapter`'s own
`trace_rpc=True` constructor argument rather than the `--tracerpc` flag
itself, which needs a live pytest session around it to read.

    TF2_INTEGRATION=1 uv run pytest tests/integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.node import free_port

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


def test_trace_rpc_prints_a_real_call_and_its_reply(
    bitcoind_path: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`trace_rpc=True` prints the real `getblockchaininfo` call and reply."""
    adapter = BitcoindAdapter(
        bitcoind_path, tmp_path / "node", free_port(), free_port(), trace_rpc=True
    )
    adapter.start()
    try:
        capsys.readouterr()  # drop whatever `start` itself already printed
        adapter.rpc.call("getblockchaininfo")
        printed = capsys.readouterr().out
        assert "getblockchaininfo" in printed
        assert "-->" in printed
        assert "<--" in printed
    finally:
        adapter.stop()
