# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Core's `interface_rpc`, one body over either node.

Read from Core's `test/functional/interface_rpc.py` (`fa2bd96cc0d4`,
2026-08-06), [ISS 14](https://github.com/btclib-org/bitcoin-node-tests/issues/14)'s:
the JSON-RPC server's own answers, each read off the HTTP exchange
rather than through a client that interprets them. `_post` sends a body
as it is written, over the node's own RPC connection and credential,
with `bitcoin_core_rpc.transport.http_request`, and reads back the
status and the body; Core's own `send_raw_rpc` does the same through its
harness's `AuthServiceProxy._request`.

- `getrpcinfo` names the one call running, itself, and the node's own
  debug log (`Capability.RPC_INFO`): Core's `test_getrpcinfo`.
- A batch is answered member by member in each member's own JSON-RPC
  version, a notification's answer left out and a batch of nothing but
  notifications answered 204: Core's `test_batch_requests`.
- A legacy request's error is an HTTP error status, a 2.0 request's is
  200, and a body that does not parse, or names no version the server
  knows, is refused with Core's own status and envelope: the first two
  steps of Core's `test_http_status_codes`.
- A 2.0 request with an `id`, even a null one, and a legacy request are
  no notification; a 2.0 notification runs and is answered 204 with no
  body, an invalid one too, running nothing: that test's last step, whose
  notification is `generatetoaddress` (`Capability.GENERATE`).
- A node with one RPC thread and a work queue of one refuses the
  request beyond them with 503 and "Work queue depth exceeded"
  (`Capability.RPC_WORK_QUEUE`): Core's `test_work_queue_exceeded`.

A smaller claim than Core's own file, declared rather than silent. Core
sends the last of these through `bitcoin-cli`, which prints a 503's body
after `Server response:`, and matches the message `TestNodeCLI.send_cli`
(`test_node.py`) rewrites that into, where this sends the same request
over `_exchange` and matches the 503 and the body the server sent; what
`bitcoin-cli` makes of it is `interface_bitcoin_cli.py`'s subject
([ISS 49](https://github.com/btclib-org/bitcoin-node-tests/issues/49)).
`http_request` returns no header, so `_post` does not check the
`Content-Type` Core's `AuthServiceProxy._get_response` checks, a check
of Core's harness rather than of any step of the test.

`interface_rpc_bitcoind_test.py` and `interface_rpc_btclib_node_test.py`
run it, `tests/integration/conftest.py`'s own module docstring having
how.
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from bitcoin_core_rpc import RPCErrorCode
from bitcoin_core_rpc.transport import http_request
from btclib.network import NETWORKS

from bitcoin_node_tests.bitcoind import BitcoindAdapter
from bitcoin_node_tests.capability import Capability, require

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from bitcoin_node_tests.btclib_node import BtclibNodeAdapter
    from bitcoin_node_tests.capability import SkipCounts

__all__ = [
    "a_batch_is_answered_member_by_member",
    "a_full_work_queue_refuses_the_request_beyond_it",
    "a_notification_runs_and_is_answered_with_no_content",
    "each_version_is_answered_with_its_own_status",
    "getrpcinfo_names_the_call_running_and_the_log",
]

type _Node = BitcoindAdapter | BtclibNodeAdapter
type _Cluster = Callable[[int], Sequence[_Node]]

_OK = 200
_NO_CONTENT = 204
_BAD_REQUEST = 400
_NOT_FOUND = 404
_INTERNAL_SERVER_ERROR = 500
_SERVICE_UNAVAILABLE = 503

_GENESIS_HASH = NETWORKS["regtest"].genesis_block.hex()

# Core's own `test_http_status_codes`: the regtest P2WPKH address of an
# all-zero key hash, and a string that is no address
_BURN_ADDRESS = "bcrt1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqdku202"
_INVALID_ADDRESS = "invalid_address"

# what `src/httpserver.cpp` sends with the 503
_WORK_QUEUE_EXCEEDED = b"Work queue depth exceeded"

# Core's own `test_work_queue_exceeded`: one caller more than the thread
# and the queue behind it hold, each waiting on `waitfornewblock` for
# this many milliseconds
_CALLERS = 3
_WAIT_MS = 500

_PARSE_ERROR_REPLY = {
    "id": None,
    "result": None,
    "error": {"code": RPCErrorCode.PARSE_ERROR, "message": "Parse error"},
}


@dataclass
class _BatchOptions:
    """Core's own `BatchOptions`: how one member of a batch is written."""

    version: int | None = None
    notification: bool = False
    request_fields: dict[str, Any] | None = None
    response_fields: dict[str, Any] | None = None


def _format_request(
    options: _BatchOptions, idx: int, fields: dict[str, Any]
) -> dict[str, Any]:
    """Return the request Core's own `format_request` writes.

    :param options: the member's version, whether it is a notification,
        and fields to write over the rest.
    :param idx: the member's `id`, where it is no notification.
    :param fields: the member's `method` and `params`.
    """
    request: dict[str, Any] = {}
    if options.version == 1:
        request.update(version="1.1")
    elif options.version == 2:
        request.update(jsonrpc="2.0")
    if not options.notification:
        request.update(id=idx)
    request.update(fields)
    if options.request_fields:
        request.update(options.request_fields)
    return request


def _format_response(
    options: _BatchOptions, idx: int, fields: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the answer Core's own `format_response` expects, or `None`.

    `None` is a 2.0 notification's, which is answered with nothing.

    :param options: what `_format_request` wrote the member with.
    :param idx: the member's `id`, where it is no notification.
    :param fields: the member's own `result` or `error`.
    """
    if options.version == 2 and options.notification:
        return None
    response: dict[str, Any] = {}
    if not options.notification:
        response.update(id=idx)
    if options.version == 2:
        response.update(jsonrpc="2.0")
    else:
        response.update(result=None, error=None)
    response.update(fields)
    if options.response_fields:
        response.update(options.response_fields)
    return response


def _exchange(node: _Node, body: bytes) -> tuple[int, bytes]:
    """Send `body` as it is written, and return the status and the body back.

    Sent with the credential and over the connection the node's own RPC
    client uses, the caller's thread's own.

    :param node: the node to send it to.
    :param body: the request's body, sent unchanged.
    """
    client = node.rpc
    return http_request(
        client.url,
        data=body,
        headers={
            "Authorization": client.auth_header(),
            "Content-Type": "application/json",
        },
        timeout=client.timeout,
        transport=client.transport,
    )


def _post(node: _Node, body: bytes) -> tuple[object, int]:
    """Return the reply `body` earns and its HTTP status, Core's `send_raw_rpc`.

    A 204's reply is `None`, and it has to have no body, as
    `AuthServiceProxy._get_response` has it; any other is the JSON the
    body holds, a fractional number decoded as a `Decimal`.

    :param node: the node to send it to.
    :param body: the request's body, sent unchanged.
    """
    status, payload = _exchange(node, body)
    if status == _NO_CONTENT:
        assert payload == b""
        return None, status
    return json.loads(payload, parse_float=Decimal), status


def _post_json(node: _Node, body: object) -> tuple[object, int]:
    """Return `_post`'s answer to `body` as JSON, Core's `send_json_rpc`.

    :param node: the node to send it to.
    :param body: a request object, or a batch of them.
    """
    return _post(node, json.dumps(body).encode())


def _expect_status(
    node: _Node,
    expected_status: int,
    expected_code: RPCErrorCode | None,
    method: str,
    params: list[Any],
    version: int = 1,
    *,
    notification: bool = False,
) -> None:
    """Send one request and check its status and its error, Core's own.

    Core's `expect_http_rpc_status`.

    :param node: the node to send it to.
    :param expected_status: the HTTP status the answer has to carry.
    :param expected_code: the error code the answer has to carry, or
        `None` where nothing is checked of the error.
    :param method: the request's method.
    :param params: the request's params.
    :param version: `1` for a legacy request, `2` for a 2.0 one.
    :param notification: whether the request carries no `id`.
    """
    options = _BatchOptions(version, notification)
    request = _format_request(options, 0, {"method": method, "params": params})
    response, status = _post_json(node, request)
    if expected_code is not None:
        assert isinstance(response, dict)
        assert response["error"]["code"] == expected_code
    assert status == expected_status


def getrpcinfo_names_the_call_running_and_the_log(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_getrpcinfo`: the one call running, and the debug log.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    :raises TypeError: the node declares `Capability.RPC_INFO` without
        being the adapter that names a `debug_log_path`.
    """
    (node,) = cluster(1)
    require(Capability.RPC_INFO, node.capabilities, skip_counts)
    if not isinstance(node, BitcoindAdapter):
        err_msg = f"{type(node).__name__} declares RPC_INFO, naming no debug.log"
        raise TypeError(err_msg)
    info = node.rpc.call("getrpcinfo")
    assert len(info["active_commands"]) == 1
    command = info["active_commands"][0]
    assert command["method"] == "getrpcinfo"
    assert command["duration"] >= 0
    assert info["logpath"] == str(node.debug_log_path)


def _batch_request(
    node: _Node, call_options: Callable[[int], _BatchOptions | None]
) -> None:
    """Send Core's own four calls as one batch, and check what comes back.

    Core's `test_batch_request`: a call that works, one naming no method
    the node has, another that works, and one that is no request at all.

    :param node: a node on a chain of the genesis block alone.
    :param call_options: how to write the member of each `id`, or `None`
        to leave it out.
    """
    calls: list[dict[str, Any]] = [
        {"method": "getblockcount"},
        {"method": "invalidmethod"},
        {"method": "getblockhash", "params": [0]},
        {"pizza": "sausage"},
    ]
    results: list[dict[str, Any]] = [
        {"result": 0},
        {
            "error": {
                "code": RPCErrorCode.METHOD_NOT_FOUND,
                "message": "Method not found",
            }
        },
        {"result": _GENESIS_HASH},
        {"error": {"code": RPCErrorCode.INVALID_REQUEST, "message": "Missing method"}},
    ]

    request = []
    response = []
    for idx, (call, result) in enumerate(zip(calls, results, strict=True), 1):
        options = call_options(idx)
        if options is None:
            continue
        request.append(_format_request(options, idx, call))
        expected = _format_response(options, idx, result)
        if expected is not None:
            response.append(expected)

    rpc_response, http_status = _post_json(node, request)
    if not response and request:
        assert http_status == _NO_CONTENT
        assert rpc_response is None
    else:
        assert http_status == _OK
        assert rpc_response == response


def a_batch_is_answered_member_by_member(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_batch_requests`: each member in its own version.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally, unread: nothing here
        asks for more than a node's own RPC.
    """
    del skip_counts
    (node,) = cluster(1)

    # an empty batch
    _batch_request(node, lambda _idx: None)
    # JSON-RPC 2.0
    _batch_request(node, lambda _idx: _BatchOptions(version=2))
    # JSON-RPC 2.0, the first member a notification
    _batch_request(node, lambda idx: _BatchOptions(version=2, notification=idx < 2))
    # JSON-RPC 2.0, every member a notification
    _batch_request(node, lambda _idx: _BatchOptions(version=2, notification=True))
    # JSON-RPC 1.1, which has no batch: kept by Core for backwards
    # compatibility
    _batch_request(node, lambda _idx: _BatchOptions(version=1))
    # 1.1 and 2.0 alternating
    _batch_request(node, lambda idx: _BatchOptions(version=2 if idx % 2 else 1))
    # no version
    _batch_request(node, lambda _idx: _BatchOptions())
    # no version and no id
    _batch_request(node, lambda _idx: _BatchOptions(notification=True))
    # `"jsonrpc": "1.0"`, accepted
    _batch_request(node, lambda _idx: _BatchOptions(request_fields={"jsonrpc": "1.0"}))
    # a version the server does not know, refused member by member
    _batch_request(
        node,
        lambda _idx: _BatchOptions(
            request_fields={"jsonrpc": "2.1"},
            response_fields={
                "result": None,
                "error": {
                    "code": RPCErrorCode.INVALID_REQUEST,
                    "message": "JSON-RPC version not supported",
                },
            },
        ),
    )


def each_version_is_answered_with_its_own_status(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_http_status_codes`, its JSON-RPC 1.1 and 2.0 requests.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally, unread: nothing here
        asks for more than a node's own RPC.
    """
    del skip_counts
    (node,) = cluster(1)

    # JSON-RPC 1.1: an error is an HTTP error status
    _expect_status(node, _OK, None, "getblockhash", [0])
    _expect_status(node, _NOT_FOUND, RPCErrorCode.METHOD_NOT_FOUND, "invalidmethod", [])
    _expect_status(
        node,
        _INTERNAL_SERVER_ERROR,
        RPCErrorCode.INVALID_PARAMETER,
        "getblockhash",
        [42],
    )
    response, status = _post(node, b"")
    assert response == _PARSE_ERROR_REPLY
    assert status == _INTERNAL_SERVER_ERROR
    response, status = _post(node, b"this is bad")
    assert response == _PARSE_ERROR_REPLY
    assert status == _INTERNAL_SERVER_ERROR

    # JSON-RPC 2.0: an error is an RPC error, and not an HTTP one
    _expect_status(node, _OK, None, "getblockhash", [0], 2)
    _expect_status(node, _OK, RPCErrorCode.METHOD_NOT_FOUND, "invalidmethod", [], 2)
    _expect_status(node, _OK, RPCErrorCode.INVALID_PARAMETER, "getblockhash", [42], 2)
    # the envelope itself refused
    response, status = _post_json(node, {"jsonrpc": 2, "method": "getblockcount"})
    assert response == {
        "result": None,
        "error": {
            "code": RPCErrorCode.INVALID_REQUEST,
            "message": "jsonrpc field must be a string",
        },
    }
    assert status == _BAD_REQUEST
    response, status = _post_json(node, {"jsonrpc": "3.0", "method": "getblockcount"})
    assert response == {
        "result": None,
        "error": {
            "code": RPCErrorCode.INVALID_REQUEST,
            "message": "JSON-RPC version not supported",
        },
    }
    assert status == _BAD_REQUEST


def a_notification_runs_and_is_answered_with_no_content(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_http_status_codes`, its JSON-RPC 2.0 notifications.

    What is no notification is checked first, on any node; a notification
    is `generatetoaddress`, so the rest asks for `Capability.GENERATE`.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)

    # an `id` of null is still an `id`
    response, status = _post_json(
        node, {"jsonrpc": "2.0", "id": None, "method": "getblockcount"}
    )
    assert isinstance(response, dict)
    assert response["result"] == 0
    assert status == _OK
    # a JSON-RPC 1.1 request is never a notification
    _expect_status(node, _OK, None, "getblockcount", [], 1)
    # nor is a 2.0 request with an `id`
    _expect_status(node, _OK, None, "getblockcount", [], 2)

    require(Capability.GENERATE, node.capabilities, skip_counts)
    block_count = node.rpc.call("getblockcount")
    _expect_status(
        node,
        _NO_CONTENT,
        None,
        "generatetoaddress",
        [1, _BURN_ADDRESS],
        2,
        notification=True,
    )
    # it ran, though nothing answered
    assert node.rpc.call("getblockcount") == block_count + 1
    # an invalid notification is not answered either
    _expect_status(
        node,
        _NO_CONTENT,
        None,
        "generatetoaddress",
        [1, _INVALID_ADDRESS],
        2,
        notification=True,
    )
    # and it did not run
    assert node.rpc.call("getblockcount") == block_count + 1


def _wait_until_refused(node: _Node, done: threading.Event) -> None:
    """Ask for `waitfornewblock` until a caller is refused, Core's own loop.

    Core's `test_work_queue_getblock`. An answer other than 200 has to be
    the 503 carrying Core's own words. Whichever caller leaves first,
    refused or failed, stops every other: one that failed leaves too few
    behind it to fill the queue again.

    :param node: a node restarted with one thread and a queue of one.
    :param done: shared by every caller, set by the first to leave.
    """
    body = json.dumps({"method": "waitfornewblock", "params": [_WAIT_MS]}).encode()
    try:
        while not done.is_set():
            status, payload = _exchange(node, body)
            if status != _OK:
                assert status == _SERVICE_UNAVAILABLE
                assert payload == _WORK_QUEUE_EXCEEDED
                return
    finally:
        done.set()


def a_full_work_queue_refuses_the_request_beyond_it(
    cluster: _Cluster, skip_counts: SkipCounts
) -> None:
    """Core's `test_work_queue_exceeded`: 503 once the queue is full.

    :param cluster: `bitcoind_cluster` or `btclib_node_cluster`.
    :param skip_counts: the session's own tally.
    """
    (node,) = cluster(1)
    require(Capability.RPC_WORK_QUEUE, node.capabilities, skip_counts)
    node.restart(["-rpcworkqueue=1", "-rpcthreads=1"])
    done = threading.Event()
    with ThreadPoolExecutor(max_workers=_CALLERS) as callers:
        futures = [
            callers.submit(_wait_until_refused, node, done) for _ in range(_CALLERS)
        ]
    for future in futures:
        future.result()
