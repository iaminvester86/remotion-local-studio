"""
extensions.py — discover and manage user-added local tools.

Drop a Python file in the `extensions/` directory that defines:

    REQUIREMENTS = ["somepkg>=1.0"]      # optional; installed via `rls ext install <name>`
    NEEDS_TORCH = False                  # optional
    def register(subparsers):            # required
        p = subparsers.add_parser("mytool", help="...")
        p.add_argument("--foo")
        p.set_defaults(func=lambda args: my_handler(args))

Dependencies stay managed: they are declared by the extension and installed into
the same venv with the same marker system as built-in features.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from .env import EXTENSIONS_DIR


def _iter_extension_files():
    if not EXTENSIONS_DIR.is_dir():
        return
    for f in sorted(EXTENSIONS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        yield f


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"rls_ext_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def load_into(subparsers) -> None:
    """Register every valid extension as a subcommand. Broken ones are skipped."""
    for f in _iter_extension_files():
        try:
            mod = _load_module(f)
            if hasattr(mod, "register"):
                mod.register(subparsers)
        except Exception as e:  # never let one extension break the whole CLI
            print(f"[rls] skipping extension {f.name}: {e}")


def list_extensions() -> list[str]:
    return [f.stem for f in _iter_extension_files()]


def install_extension(name: str) -> int:
    from .deps import ensure_packages
    path = EXTENSIONS_DIR / f"{name}.py"
    if not path.is_file():
        raise SystemExit(f"No extension named '{name}' in {EXTENSIONS_DIR}")
    mod = _load_module(path)
    reqs = list(getattr(mod, "REQUIREMENTS", []))
    if not reqs:
        print(f"[rls] extension '{name}' declares no REQUIREMENTS; nothing to install.")
        return 0
    ensure_packages(f"ext_{name}", reqs, need_torch=bool(getattr(mod, "NEEDS_TORCH", False)))
    print(f"[rls] extension '{name}' dependencies installed.")
    return 0
