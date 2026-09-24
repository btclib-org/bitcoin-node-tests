# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every module and package of bitcoin_node_tests declares an `__all__`.

A name is public here because a list says so, not because it happens to
lack a leading underscore. This step carries one module, the package
root, whose `__all__` is empty; a census walks the tree rather than
listing it, so a submodule a later step adds without exporting it fails
here until it is.
"""

from __future__ import annotations

import ast
from pathlib import Path

import bitcoin_node_tests

_PACKAGE_DIR = Path(bitcoin_node_tests.__file__).parent


def _declares_all(path: Path) -> bool:
    """Return whether a module's source declares a module-level `__all__`.

    Parsed rather than imported, so a module that is not yet importable
    still gets a verdict.

    :param path: the module's source file.
    :returns: whether an `__all__` assignment sits at module level.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.Assign | ast.AnnAssign)
        and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
        )
        for node in tree.body
    )


def test_every_module_declares_all() -> None:
    """Every `.py` file under the package declares its own `__all__`."""
    missing = [
        path.relative_to(_PACKAGE_DIR)
        for path in sorted(_PACKAGE_DIR.rglob("*.py"))
        if not _declares_all(path)
    ]
    assert not missing, f"no __all__ declared in: {missing}"


def test_the_root_all_is_empty() -> None:
    """This step ships no submodule, so the root publishes nothing yet.

    A later step's addition is what makes this list non-empty, and the
    census above is what then asks whether every module below it
    declares its own.
    """
    assert bitcoin_node_tests.__all__ == []
