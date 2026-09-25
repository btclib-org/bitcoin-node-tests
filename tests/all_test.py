# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every module and package of bitcoin_node_tests declares an `__all__`.

A name is public here because a list says so, not because it happens to
lack a leading underscore. The package root's own `__all__` is empty by
decision, not by omission: a caller imports the submodule it needs
rather than a name re-exported off the root. A census walks the tree
rather than listing it, so a submodule added later without exporting
its own public names fails here until it does.
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
    """The root re-exports nothing: a caller imports the submodule it needs.

    The census above is what asks whether every module below the root
    declares its own `__all__`; this is what says the root itself holds
    no re-export of any of them.
    """
    assert bitcoin_node_tests.__all__ == []
