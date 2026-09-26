# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every adapter `tests/integration/` builds is built with `--tracerpc`.

[ISS 89](https://github.com/btclib-org/bitcoin-node-tests/issues/89):
`NodeAdapter` takes `trace_rpc` per instance, so an adapter constructed
without it never traces, whatever the command line says. The
`make_adapter` fixture is what passes the option on; this module is the
AST walk that holds every construction under `tests/integration/` to
going through it, or to naming its own `trace_rpc` --
`tracerpc_option_bitcoind_test.py`'s own `trace_rpc=True`, which proves
the wrapper whether or not the flag was given. Parsed rather than
imported, since the files it reads skip themselves without
`TF2_INTEGRATION=1`.

An adapter class is a name ending in `Adapter`, or a class the module
itself derives from one, whatever it is called.
"""

from __future__ import annotations

import ast
from pathlib import Path

_INTEGRATION = Path(__file__).parent / "integration"


def _adapter_classes(tree: ast.Module) -> set[str]:
    """Return every class `tree` defines on top of an adapter class."""
    derived: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ClassDef)
                and node.name not in derived
                and any(_is_adapter(ast.unparse(b), derived) for b in node.bases)
            ):
                derived.add(node.name)
                changed = True
    return derived


def _is_adapter(callee: str, derived: set[str]) -> bool:
    """Return whether `callee`, as written, names an adapter class."""
    return callee.endswith("Adapter") or callee.rsplit(".", 1)[-1] in derived


def _untraced(root: Path) -> list[str]:
    """Return one "file.py:line" per construction that drops `--tracerpc`."""
    found: list[str] = []
    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        derived = _adapter_classes(tree)
        found.extend(
            f"{path.name}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _is_adapter(ast.unparse(node.func), derived)
            and not any(k.arg == "trace_rpc" for k in node.keywords)
        )
    return sorted(found)


def test_every_integration_adapter_is_built_with_tracerpc() -> None:
    """No adapter under tests/integration/ bypasses `make_adapter`."""
    untraced = _untraced(_INTEGRATION)
    assert not untraced, "built without make_adapter or trace_rpc: " + ", ".join(
        untraced
    )


def test_untraced_flags_a_direct_construction(tmp_path: Path) -> None:
    """`BitcoindAdapter(...)`, bare or through its module, is flagged."""
    (tmp_path / "x_test.py").write_text(
        "a = BitcoindAdapter(p, d, 1, 2)\n"
        "b = bitcoind.BtclibNodeAdapter(p, d, 1, 2, extra_args=())\n"
    )
    assert _untraced(tmp_path) == ["x_test.py:1", "x_test.py:2"]


def test_untraced_flags_a_derived_class_of_any_name(tmp_path: Path) -> None:
    """A module's own subclass is an adapter, whatever its name."""
    (tmp_path / "x_test.py").write_text(
        "class _Onion(BitcoindAdapter):\n"
        "    pass\n"
        "class _Deeper(_Onion):\n"
        "    pass\n"
        "a = _Onion(p, d, 1, 2)\n"
        "b = _Deeper(p, d, 1, 2)\n"
    )
    assert _untraced(tmp_path) == ["x_test.py:5", "x_test.py:6"]


def test_untraced_is_silent_through_make_adapter(tmp_path: Path) -> None:
    """The same constructions, through the fixture, are not flagged."""
    (tmp_path / "x_test.py").write_text(
        "a = make_adapter(BitcoindAdapter, p, d, 1, 2)\n"
        "b = make_adapter(_Onion, p, d, 1, 2, extra_args=())\n"
    )
    assert _untraced(tmp_path) == []


def test_untraced_is_silent_on_an_explicit_trace_rpc(tmp_path: Path) -> None:
    """A construction naming its own `trace_rpc` has decided it."""
    (tmp_path / "x_test.py").write_text(
        "a = BitcoindAdapter(p, d, 1, 2, trace_rpc=True)\n"
    )
    assert _untraced(tmp_path) == []
