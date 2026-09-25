# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`assert_debug_log` over a plain file, no node involved."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bitcoin_node_tests.debug_log import _POLL_INTERVAL, assert_debug_log

if TYPE_CHECKING:
    from pathlib import Path


def test_passes_when_the_block_appends_the_expected_substring(tmp_path: Path) -> None:
    """Found on the very first read: no poll, no wait."""
    log_path = tmp_path / "debug.log"
    log_path.write_text("before\n")
    with (
        assert_debug_log(log_path, ["expected"]),
        log_path.open("a", encoding="utf-8") as log_file,
    ):
        log_file.write("expected line\n")


def test_ignores_a_match_that_was_already_there_before_entry(tmp_path: Path) -> None:
    """A substring present before the context started does not satisfy it."""
    log_path = tmp_path / "debug.log"
    log_path.write_text("expected, already here\n")
    with (
        pytest.raises(AssertionError, match="not found"),
        assert_debug_log(log_path, ["expected"], timeout=-1),
    ):
        pass


def test_works_when_the_log_does_not_exist_yet(tmp_path: Path) -> None:
    """No file at entry: `start_size` is 0 rather than a raise on it."""
    log_path = tmp_path / "debug.log"
    with assert_debug_log(log_path, ["hello"]):
        log_path.write_text("hello world\n")


def test_polls_until_the_substring_appears(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not there on the first read: this sleeps and reads again, once."""
    log_path = tmp_path / "debug.log"
    log_path.write_text("")
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("expected\n")

    monkeypatch.setattr("time.sleep", fake_sleep)
    with assert_debug_log(log_path, ["expected"], timeout=5):
        pass
    assert sleeps == [_POLL_INTERVAL]


def test_raises_when_the_substring_never_appears(tmp_path: Path) -> None:
    """A negative deadline: never enters the poll, and names what is missing."""
    log_path = tmp_path / "debug.log"
    log_path.write_text("unrelated\n")
    with (
        pytest.raises(AssertionError, match=r"\['missing'\] not found"),
        assert_debug_log(log_path, ["missing"], timeout=-1),
    ):
        pass
