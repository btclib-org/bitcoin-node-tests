# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""What the whole suite shares: a hypothesis profile, a coverage gate.

The gate is `coverage_fail_under` and the guard on it. coverage looks
for its configuration in the directory the process started in, so a run
started from `tests/` finds no `fail_under`, no `source` and no
`branch = true`. Section 8 of the organization standard leaves a tree to
point such a run at its configuration or to make it say it is ungated,
and this file is the second of the two: such a run is refused
(btclib-org/.github#443).
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import pytest
from hypothesis import settings

from bitcoin_node_tests.capability import MissingCapabilityError

settings.register_profile("default", deadline=None, max_examples=500)
settings.register_profile("thorough", deadline=None, max_examples=2_000)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture(autouse=True)
def _translate_missing_capability() -> Iterator[None]:
    """Turn `capability.require`'s own exception into an actual skip.

    `capability.py` raises `MissingCapabilityError` rather than calling
    `pytest.skip` itself, so that importing it -- `sphinx-build`'s own
    `autodoc`, among others -- never needs `pytest` installed; this is
    the one place that exception meets a pytest session, a yield fixture
    wrapping every test's own call so that an exception the test body
    raises is caught here exactly where a `try`/`except` around a
    generator's `yield` always catches one.
    """
    try:
        yield
    except MissingCapabilityError as exc:
        pytest.skip(str(exc))


def asks_for_everything(
    file_or_dir: list[str] | None, testpaths: list[str], rootpath: Path
) -> bool:
    """Whether the paths named on the command line take the suite in.

    No path at all narrows nothing and is the whole run. A path above one
    of them -- `pytest .`, or the rootdir spelled out -- collects it too,
    so what decides is containment and not equality.

    :param file_or_dir: the paths given on the command line, or `None`
        on the `--help` path, where argument parsing was abandoned.
    :param testpaths: the configured test paths, relative to the rootdir.
    :param rootpath: the pytest rootdir.
    :returns: whether the run collects the whole suite.
    """
    given = [Path(path).resolve() for path in file_or_dir or []]
    if not given:
        return True
    wanted = [(rootpath / path).resolve() for path in testpaths]
    if not wanted:
        return False
    return all(
        any(target == path or path in target.parents for path in given)
        for target in wanted
    )


def coverage_fail_under(
    asked: float | None,
    configured: float | None,
    file_or_dir: list[str] | None,
    keyword: str,
    markexpr: str,
    deselect: list[str] | None,
    ignore: list[str] | None,
    ignore_glob: list[str] | None,
    lf: bool,
    testpaths: list[str],
    rootpath: Path,
) -> float | None:
    """Return the coverage threshold this run's selection has to meet.

    A run that leaves tests out measures the same source with fewer
    tests, so its report is gated at zero instead of at `fail_under`,
    which a whole run is handed back untouched.

    :param asked: an explicit `--cov-fail-under`, honoured either way.
    :param configured: `fail_under` as pytest-cov read it from
        `pyproject.toml`.
    :param file_or_dir: the paths given on the command line.
    :param keyword: `-k`.
    :param markexpr: `-m`.
    :param deselect: `--deselect`.
    :param ignore: `--ignore`.
    :param ignore_glob: `--ignore-glob`.
    :param lf: `--lf`.
    :param testpaths: the configured test paths.
    :param rootpath: the pytest rootdir.
    :returns: the threshold this run is held to.
    """
    if asked is not None:
        return asked
    if keyword or markexpr or deselect or ignore or ignore_glob or lf:
        return 0
    if not asks_for_everything(file_or_dir, testpaths, rootpath):
        return 0
    return configured


class CoverageConfiguration(Protocol):
    """What this file reads of coverage's own configuration object."""

    config_file: str | None


def coverage_configuration(config: pytest.Config) -> CoverageConfiguration | None:
    """Return the configuration coverage is measuring with, or `None`.

    :param config: the pytest session configuration.
    :returns: the configuration object, or `None` where `--no-cov` was
        given or the plugin never registered.
    """
    plugin = config.pluginmanager.getplugin("_cov")
    controller = getattr(plugin, "cov_controller", None)
    if controller is None:
        return None
    measuring: CoverageConfiguration = controller.cov.config
    return measuring


def configuration_went_unread(
    cov_config: CoverageConfiguration | None,
    inipath: Path | None,
    asked: float | None,
    asked_for_help: bool,
    collect_only: bool,
) -> bool:
    """Return whether a run held to the floor cannot see one.

    :param cov_config: what `coverage_configuration` answered.
    :param inipath: the configuration file pytest read.
    :param asked: an explicit `--cov-fail-under`.
    :param asked_for_help: whether `--help` was given.
    :param collect_only: whether `--collect-only` was given.
    :returns: whether the floor is unreachable for this run.
    """
    if cov_config is None:
        return False
    if asked is not None:
        return False
    if asked_for_help or collect_only:
        return False
    return cov_config.config_file is None and inipath is not None


def pytest_configure(config: pytest.Config) -> None:
    """Gate a whole run at `fail_under`, and a partial one at nothing.

    :param config: the pytest session configuration.
    :raises pytest.UsageError: where coverage read no configuration.
    """
    if configuration_went_unread(
        coverage_configuration(config),
        config.inipath,
        config.option.cov_fail_under,
        config.option.help,
        config.option.collectonly,
    ):
        raise pytest.UsageError(
            "coverage read no configuration, so this run is held to no floor"
            " and measures a different set of files: coverage looks only in"
            f" the directory the run started in, {Path.cwd()}, and pytest"
            f" read {config.inipath}. Run from {config.rootpath};"
            " --cov-config restores the floor and not the file set, a"
            " relative omit pattern being resolved against the directory"
            " the run started in."
        )
    namespace = config.known_args_namespace
    namespace.cov_fail_under = coverage_fail_under(
        config.option.cov_fail_under,
        namespace.cov_fail_under,
        config.option.file_or_dir,
        config.option.keyword,
        config.option.markexpr,
        config.option.deselect,
        config.option.ignore,
        config.option.ignore_glob,
        getattr(config.option, "lf", False),
        config.getini("testpaths"),
        config.rootpath,
    )
