# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

r"""Compare a btclib-node run of `tests/integration` with `TF2.md`'s column.

`node-integration.yml`'s `btclib-node` and `btclib-node-main` jobs run
every `*_btclib_node_test.py` module, and some of those tests fail by
design: a **fail** row of `TF2.md`'s per-test ledger is a disagreement
filed on btclib-node's own tracker, and a **not ported** one a stub
ending in `pytest.fail`. So pytest's own exit status says nothing about
whether anything changed. This script says it instead: each row of the
ledger's `btclib-node` column against the testcases of the JUnit report
that row covers, printing every row whose outcome moved.

**Which verdict a cell gives for which build.** A cell is either a
single verdict, true of every build, or `; `-separated segments, each
qualified by the build it is for, in the spelling the ledger's cells
use:

- `<verdict> on the build` -- the build the row was measured against,
  the PyPI release the `btclib-node` job installs (`release` below);
- `<verdict> on a build past [ISS ...](...)`, optionally followed by
  `and before [ISS ...](...)` -- a build carrying the first fix, and
  not the second.

The `btclib-node-main` job installs btclib-node's own `main`, read here
(`main` below) as a build past every issue a cell names: its segment is
the one bounded by `past` alone. Where `main` is not past one of them,
that row reports a move, which is what the ledger's cell then owes.

A verdict is `pass`, `skip` with or without a parenthetical,
`fail ([ISS ...](...))` or `not ported`; `bitcoind only` is a whole cell
naming no btclib-node test at all. A cell or a segment in any other
shape raises `LedgerError` rather than being read as some verdict: a
cell this cannot read is a row nothing compares. The parenthetical of a
skip is the ledger's own shorthand (`blk` for `Capability.BLK_FILES`),
not a `Capability` value, so which capability refused is not compared.

**What a row's outcome is.** A row's testcases are read together: the
row failed where any of them failed, skipped where none failed and any
skipped, and passed where every one passed. A **skip** row can hold a
passing test beside the skipping one -- `feature_blocksdir.py`'s own
refusal passes on both nodes -- and a **fail** row needs one failing
test, not every one. A **fail** and a **not ported** row both expect
the row to fail.

**Which testcase is which row's.** A JUnit testcase names a module and a
function, a ledger row a Core file and a qualifier, and nothing in either
names the other, so `_ROWS` states the pairing: a module stem, less its
`_btclib_node_test` suffix, for a module whose every test is one row's,
and `module::function` where one module's tests are several rows'. A
module with no ledger row at all is in `_NO_ROW`, and its testcases are
reported only where they fail. `btclib_node_verdict_test.py` holds the
table to the tree both ways: every test function of every
`*_btclib_node_test.py` module resolves, and every ledger row other than
**bitcoind only** is some test's.

It exits 1 wherever anything moved, a row that now passes included:
each move is a cell of `TF2.md` no longer describing that build, and a
green step then means the whole column does. This writes to stdout
alone, and the workflow step copies it into `$GITHUB_STEP_SUMMARY`:

    python .github/scripts/btclib_node_verdict.py \
        TF2.md integration.xml release
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

BUILDS = ("release", "main")

_SECTION = "## The per-test ledger"

_ISS = r"\[ISS [^\]]+\]\([^)\s]+\)"

# a verdict, and the outcome a row's testcases are expected to have
_VERDICTS = (
    (re.compile(r"pass"), "pass"),
    (re.compile(r"not ported"), "fail"),
    (re.compile(rf"fail \({_ISS}\)"), "fail"),
    (re.compile(r"skip(?: \(\w+\))?"), "skip"),
)

_ON_THE_BUILD = re.compile(r"(?P<verdict>.+) on the build")
_ON_A_BUILD_PAST = re.compile(
    rf"(?P<verdict>.+) on a build past {_ISS}(?P<before> and before {_ISS})?"
)

_BITCOIND_ONLY = "bitcoind only"

_SUFFIX = "_btclib_node_test"

# a module stem, or `stem::function`, against the ledger row its tests
# are -- the row's own first cell, verbatim. A function entry wins over
# its module's
_ROWS: dict[str, str] = {
    "feature_blocksdir": "`feature_blocksdir.py`",
    "feature_filelock": "`feature_filelock.py`",
    "rpc_whitelist": "`rpc_whitelist.py`",
    "rpc_users": "`rpc_users.py`",
    "rpc_users::test_norpcauth_disables_previous_rpcauth": (
        "`rpc_users.py` (`-norpcauth`)"
    ),
    "rpc_users::test_rpcuser_rpcpassword_authenticates_without_a_cookie": (
        "`rpc_users.py` (`-rpcuser`/`-rpcpassword`)"
    ),
    "rpc_users::test_norpccookiefile_writes_no_cookie_and_rpcauth_still_authenticates": (
        "`rpc_users.py` (`-norpccookiefile`)"
    ),
    "p2p_block_sync": "`p2p_block_sync.py`",
    "p2p_compactblocks_hb": "`p2p_compactblocks_hb.py`",
    "p2p_getdata": "`p2p_getdata.py`",
    "p2p_invalid_locator": "`p2p_invalid_locator.py`",
    "p2p_invalid_messages::test_wrong_magic_bytes_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (wire)"
    ),
    "p2p_invalid_messages::test_wrong_magic_bytes_is_logged": (
        "`p2p_invalid_messages.py` (log)"
    ),
    "p2p_invalid_messages::test_oversized_message_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (size, wire)"
    ),
    "p2p_invalid_messages::test_oversized_message_is_logged": (
        "`p2p_invalid_messages.py` (size, log)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_inv_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (inv, wire)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_inv_is_logged": (
        "`p2p_invalid_messages.py` (inv, log)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_getdata_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (getdata, wire)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_getdata_is_logged": (
        "`p2p_invalid_messages.py` (getdata, log)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_headers_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (headers, wire)"
    ),
    "p2p_invalid_messages_misbehaving::test_oversized_headers_is_logged": (
        "`p2p_invalid_messages.py` (headers, log)"
    ),
    "p2p_invalid_messages_misbehaving::test_invalid_pow_header_disconnects_the_peer": (
        "`p2p_invalid_messages.py` (invalid pow, wire)"
    ),
    "p2p_invalid_messages_misbehaving::test_invalid_pow_header_is_logged": (
        "`p2p_invalid_messages.py` (invalid pow, log)"
    ),
    "p2p_invalid_messages_dropped::test_duplicate_version_keeps_the_connection": (
        "`p2p_invalid_messages.py` (dup version, wire)"
    ),
    "p2p_invalid_messages_dropped::test_duplicate_version_is_logged": (
        "`p2p_invalid_messages.py` (dup version, log)"
    ),
    "p2p_invalid_messages_dropped::test_wrong_checksum_keeps_the_connection": (
        "`p2p_invalid_messages.py` (checksum, wire)"
    ),
    "p2p_invalid_messages_dropped::test_wrong_checksum_is_logged": (
        "`p2p_invalid_messages.py` (checksum, log)"
    ),
    "p2p_invalid_messages_dropped::test_invalid_msgtype_keeps_the_connection": (
        "`p2p_invalid_messages.py` (msgtype, wire)"
    ),
    "p2p_invalid_messages_dropped::test_invalid_msgtype_is_logged": (
        "`p2p_invalid_messages.py` (msgtype, log)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_empty_keeps_the_connection": (
        "`p2p_invalid_messages.py` (addrv2 empty, wire)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_empty_is_logged": (
        "`p2p_invalid_messages.py` (addrv2 empty, log)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_no_addresses_keeps_the_connection": (
        "`p2p_invalid_messages.py` (addrv2 no addr, wire)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_no_addresses_is_logged": (
        "`p2p_invalid_messages.py` (addrv2 no addr, log)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_too_long_address_keeps_the_connection": (
        "`p2p_invalid_messages.py` (addrv2 long, wire)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_too_long_address_is_logged": (
        "`p2p_invalid_messages.py` (addrv2 long, log)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_unrecognized_network_keeps_the_connection": (
        "`p2p_invalid_messages.py` (addrv2 net id, wire)"
    ),
    "p2p_invalid_messages_addrv2::test_addrv2_unrecognized_network_is_logged": (
        "`p2p_invalid_messages.py` (addrv2 net id, log)"
    ),
    "p2p_leak::test_obsolete_version_disconnects_the_peer": "`p2p_leak.py` (wire)",
    "p2p_leak::test_obsolete_version_is_logged": "`p2p_leak.py` (log)",
    "p2p_handshake::test_redundant_verack_keeps_the_connection": (
        "`p2p_handshake.py` (wire)"
    ),
    "p2p_handshake::test_redundant_verack_is_logged": ("`p2p_handshake.py` (log)"),
    "p2p_addr_relay::test_oversized_addr_disconnects_the_peer": (
        "`p2p_addr_relay.py` (wire)"
    ),
    "p2p_addr_relay::test_oversized_addr_is_logged": ("`p2p_addr_relay.py` (log)"),
    "p2p_addrv2_relay::test_sendaddrv2_after_verack_disconnects_the_peer": (
        "`p2p_addrv2_relay.py` (wire)"
    ),
    "p2p_addrv2_relay::test_sendaddrv2_after_verack_is_logged": (
        "`p2p_addrv2_relay.py` (log)"
    ),
    "p2p_net_deadlock": "`p2p_net_deadlock.py`",
    "feature_uacomment": "`feature_uacomment.py`",
    "rpc_uptime": "`rpc_uptime.py`",
    "feature_framework_miniwallet": "`feature_framework_miniwallet.py`",
    "mempool_resurrect": "`mempool_resurrect.py`",
    "mempool_spend_coinbase": "`mempool_spend_coinbase.py`",
    "feature_dersig::test_dersig_activates_one_block_before_the_configured_height": (
        "`feature_dersig.py`"
    ),
    "feature_dersig::test_a_block_below_the_minimum_version_is_refused": (
        "`feature_dersig.py` (wire)"
    ),
    "feature_dersig::test_a_block_below_the_minimum_version_is_logged": (
        "`feature_dersig.py` (log)"
    ),
    "feature_dersig::test_a_non_der_signature_is_refused_once_active": (
        "`feature_dersig.py` (signature)"
    ),
    "feature_cltv::test_cltv_activates_one_block_before_the_configured_height": (
        "`feature_cltv.py`"
    ),
    "feature_cltv::test_a_version_3_block_is_refused_once_active": (
        "`feature_cltv.py` (wire)"
    ),
    "feature_cltv::test_a_version_3_block_is_logged_once_active": (
        "`feature_cltv.py` (log)"
    ),
    "feature_csv_activation": "`feature_csv_activation.py`",
    "feature_nulldummy": "`feature_nulldummy.py`",
    "feature_dirsymlinks": "`feature_dirsymlinks.py`",
    "feature_posix_fs_permissions": "`feature_posix_fs_permissions.py`",
    "rpc_setban::test_a_ban_drops_the_connection_it_matches": "`rpc_setban.py` (ban)",
    "rpc_setban::test_a_ban_survives_a_restart_until_it_is_removed": (
        "`rpc_setban.py` (restart)"
    ),
    "rpc_setban::test_a_noban_permission_reconnects_a_banned_peer": (
        "`rpc_setban.py` (noban)"
    ),
    "rpc_setban::test_a_non_ip_address_can_be_banned_and_unbanned": (
        "`rpc_setban.py` (non-IP)"
    ),
    "rpc_setban::test_bantime_given_at_a_restart_sets_a_new_ban_s_duration": (
        "`rpc_setban.py` (bantime)"
    ),
    "p2p_disconnect_ban": "`p2p_disconnect_ban.py` (disconnectnode)",
    "mempool_datacarrier": "`mempool_datacarrier.py`",
    "mempool_dust": "`mempool_dust.py`",
    "mempool_sigoplimit": "`mempool_sigoplimit.py`",
    "mempool_package_limits": "`mempool_package_limits.py`",
    "mempool_updatefromblock": "`mempool_updatefromblock.py`",
    "p2p_leak_tx::test_tx_in_block": "`p2p_leak_tx.py` (in block)",
    "p2p_leak_tx::test_notfound_on_replaced_tx": "`p2p_leak_tx.py` (replaced)",
    "p2p_leak_tx::test_notfound_on_unannounced_tx": "`p2p_leak_tx.py` (unannounced)",
    "feature_utxo_set_hash": "`feature_utxo_set_hash.py`",
    "rpc_getdescriptoractivity": "`rpc_getdescriptoractivity.py`",
    "rpc_getdescriptoractivity::test_activity_in_block": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getdescriptoractivity::test_no_mempool_inclusion": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getdescriptoractivity::test_multiple_addresses": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getdescriptoractivity::test_confirmed_and_unconfirmed": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getdescriptoractivity::test_receive_then_spend": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getdescriptoractivity::test_no_address": (
        "`rpc_getdescriptoractivity.py` (mempool)"
    ),
    "rpc_getblockstats": "`rpc_getblockstats.py`",
    "feature_fastprune": "`feature_fastprune.py`",
    "rpc_scanblocks": "`rpc_scanblocks.py`",
    "rpc_scanblocks::test_scanblocks_refuses_without_the_index": (
        "`rpc_scanblocks.py` (no index)"
    ),
    "p2p_eviction": "`p2p_eviction.py`",
    "feature_presegwit_node_upgrade": "`feature_presegwit_node_upgrade.py`",
    "rpc_validateaddress": "`rpc_validateaddress.py`",
    "p2p_addrfetch": "`p2p_addrfetch.py`",
    "rpc_echo_payload": "`rpc_echo_payload.py`",
}

# the modules whose tests are this repository's own harness rather than
# a port of a Core test, so no ledger row covers them
_NO_ROW = frozenset(
    {
        "adapter_lifecycle",
        "chain_selection",
        "mempool_fill",
        "mixed_cluster_block_sync",
        "v2transport_option",
    }
)


class LedgerError(ValueError):
    """A per-test ledger row, or a `btclib-node` cell, this cannot read."""


@dataclass(frozen=True)
class Expected:
    """What a ledger cell expects of a row's testcases on one build.

    :param text: the cell's own verdict for that build, as the ledger
        spells it.
    :param outcome: `"pass"`, `"fail"` or `"skip"`.
    """

    text: str
    outcome: str


def _verdict(row: str, text: str) -> Expected:
    """Read one verdict, less any build qualifier.

    :param row: the row's own first cell, named in a refusal.
    :param text: the verdict.
    :returns: the verdict and the outcome it expects.
    :raises LedgerError: where the text is no verdict the ledger defines.
    """
    for pattern, outcome in _VERDICTS:
        if pattern.fullmatch(text):
            return Expected(text, outcome)
    msg = f"{row}: no verdict reads {text!r}"
    raise LedgerError(msg)


def expected(row: str, cell: str, build: str) -> Expected | None:
    """Return what a `btclib-node` cell expects on one build.

    :param row: the row's own first cell, named in a refusal.
    :param cell: the row's `btclib-node` cell.
    :param build: `"release"` or `"main"`.
    :returns: the verdict for that build, or None for **bitcoind only**.
    :raises LedgerError: where a segment is in no shape the ledger
        defines, or where the cell does not give that build exactly one
        verdict.
    """
    if cell == _BITCOIND_ONLY:
        return None
    segments = cell.split("; ")
    if len(segments) == 1 and " on " not in cell:
        return _verdict(row, cell)
    found: list[str] = []
    for segment in segments:
        if match := _ON_THE_BUILD.fullmatch(segment):
            if build == "release":
                found.append(match["verdict"])
        elif match := _ON_A_BUILD_PAST.fullmatch(segment):
            if build == "main" and match["before"] is None:
                found.append(match["verdict"])
        else:
            msg = f"{row}: no build qualifier reads {segment!r}"
            raise LedgerError(msg)
    if len(found) != 1:
        msg = f"{row}: {cell!r} gives the {build} build {len(found)} verdicts"
        raise LedgerError(msg)
    return _verdict(row, found[0])


def ledger_cells(ledger_text: str) -> dict[str, str]:
    """Return each per-test ledger row's first cell, with its btclib-node cell.

    :param ledger_text: `TF2.md`'s own text.
    :returns: each row's first cell against its `btclib-node` cell.
    :raises LedgerError: where the section is missing, where a row does
        not have the table's own width, or where two rows share a first
        cell.
    """
    if _SECTION not in ledger_text:
        msg = f"no {_SECTION!r} section"
        raise LedgerError(msg)
    section = ledger_text.split(_SECTION, 1)[1].split("\n## ", 1)[0]
    cells: dict[str, str] = {}
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        row = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(row) != 5:
            msg = f"a row of {len(row)} cells, not five: {line!r}"
            raise LedgerError(msg)
        if row[0] in cells:
            msg = f"two rows read {row[0]}"
            raise LedgerError(msg)
        cells[row[0]] = row[4]
    return cells


def parse_junit(path: Path) -> dict[str, str]:
    """Return `{"classname::name": status}` for every testcase a report holds.

    :param path: the JUnit XML report's own path.
    :returns: `"fail"` where a `<failure>` or an `<error>` child is
        present, `"skip"` where a `<skipped>` one is, `"pass"` otherwise.
    """
    root = ET.parse(path).getroot()  # noqa: S314
    results: dict[str, str] = {}
    for case in root.iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None or case.find("error") is not None:
            status = "fail"
        elif case.find("skipped") is not None:
            status = "skip"
        else:
            status = "pass"
        results[key] = status
    return results


def locate(key: str) -> tuple[str, str]:
    """Return a testcase's module stem and its function.

    :param key: `parse_junit`'s own `classname::name`, a parametrized
        name carrying its `[id]`.
    :returns: the module's stem less `_btclib_node_test`, and the
        function's name less any `[id]`.
    """
    classname, name = key.split("::", 1)
    return classname.rsplit(".", 1)[-1].removesuffix(_SUFFIX), name.split("[", 1)[0]


def row_of(stem: str, function: str) -> str | None:
    """Return the ledger row a test function is, from `_ROWS`.

    :param stem: the module's stem less `_btclib_node_test`.
    :param function: the test function's own name.
    :returns: the row's first cell, or None where `_ROWS` names neither
        the function nor its module.
    """
    return _ROWS.get(f"{stem}::{function}", _ROWS.get(stem))


def _outcome(statuses: list[str]) -> str:
    """Return a row's outcome from its testcases' own statuses."""
    if "fail" in statuses:
        return "fail"
    if "skip" in statuses:
        return "skip"
    return "pass"


_KIND = {
    ("pass", "fail"): "regression",
    ("pass", "skip"): "skipped",
    ("fail", "pass"): "fixed",
    ("fail", "skip"): "skipped",
    ("skip", "pass"): "ran",
    ("skip", "fail"): "ran, and failed",
}


def moves(ledger_text: str, results: dict[str, str], build: str) -> list[str]:
    """Return one report line per row, or testcase, that moved.

    :param ledger_text: `TF2.md`'s own text.
    :param results: `parse_junit`'s reading of the report.
    :param build: `"release"` or `"main"`, the build the report ran.
    :returns: the lines, one per ledger row whose outcome differs from
        its cell's verdict for that build, per row no testcase of the
        report reached, and per testcase `_ROWS` has no row for.
    :raises LedgerError: where a cell is in no shape the ledger defines.
    """
    by_row: dict[str, dict[str, str]] = {}
    lines: list[str] = []
    for key, status in sorted(results.items()):
        stem, function = locate(key)
        row = row_of(stem, function)
        if row is not None:
            by_row.setdefault(row, {})[key.split("::", 1)[1]] = status
        elif stem not in _NO_ROW:
            lines.append(
                f"- **no row**: `{key}` is a testcase `_ROWS` names no row for"
            )
        elif status == "fail":
            lines.append(f"- **no row**: `{key}` fails, and no ledger row covers it")
    for row, cell in ledger_cells(ledger_text).items():
        verdict = expected(row, cell, build)
        if verdict is None:
            continue
        cases = by_row.get(row)
        if not cases:
            lines.append(f"- **missing**: {row} -- no testcase of this report is its")
            continue
        outcome = _outcome(list(cases.values()))
        if outcome == verdict.outcome:
            continue
        names = ", ".join(
            f"`{name}`" for name, status in cases.items() if status == outcome
        )
        lines.append(
            f"- **{_KIND[verdict.outcome, outcome]}**: {row} -- TF2.md reads"
            f" {verdict.text}; this run's outcome is {outcome}: {names}"
        )
    return lines


def main() -> int:
    """Compare the report with the ledger, and print what moved.

    It exits 1 where anything moved, and 0 where nothing did.
    A usage error is the only way this exits 2, the workflow step passing
    all three arguments every time.
    """
    args = sys.argv[1:]
    if len(args) != 3 or args[2] not in BUILDS:
        print(
            f"usage: {Path(sys.argv[0]).name} <TF2.md> <junit.xml> <release|main>",
            file=sys.stderr,
        )
        return 2
    ledger_path, report_path, build = Path(args[0]), Path(args[1]), args[2]
    lines = moves(
        ledger_path.read_text(encoding="utf-8"), parse_junit(report_path), build
    )
    print(f"### TF2.md's btclib-node column against the {build} build")
    print()
    if not lines:
        print("Nothing moved: every row agrees with TF2.md.")
        return 0
    print("Moved since TF2.md:")
    print()
    for line in lines:
        print(line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
