# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The bitcoin_node_tests package: tf2, and the version metadata.

Core's functional tests, rewritten on `btclib`, run against any node that
speaks bitcoin's RPC and p2p (issue btclib-org/btclib#2220). It imports
`btclib` and `bitcoin-core-rpc`; it imports no node, reaching one only
over a process, an RPC socket or a p2p socket.

This step carries the organization's apparatus and the ledger of what
Core's `test/functional/test_framework/` needs and what covers it; the
adapter, the test families and the rest are later steps, and this
package publishes nothing yet. `__all__` is empty rather than absent, so
that a later step's addition is the only thing that changes it.

`name` and the metadata dunders are not in `__all__`: each is still an
attribute here, `bitcoin_node_tests.__version__` being how a caller reads
the version.
"""

from importlib.metadata import PackageNotFoundError, version

name = "bitcoin_node_tests"
# read back from the installed distribution, so that pyproject.toml is
# the only place the version is written
try:
    __version__ = version("bitcoin-node-tests")
except PackageNotFoundError:
    # git clone and import, with nothing installed: any number here would
    # be a guess, and importing has to keep working
    __version__ = "unknown"

__all__: list[str] = []
