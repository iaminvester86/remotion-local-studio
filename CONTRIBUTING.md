# Contributing

Guiding constraint: **no required paid APIs**. The default path stays fully local.

## Principles
- Base install must stay tiny. CPU-friendly tools go in `requirements.txt`; heavy
  GPU tools install on demand through `rls install` / `deps.py`.
- Heavy libraries are imported lazily inside handlers, never at import time, so the
  CLI runs on a bare interpreter.
- Document hardware needs and quality honestly in `docs/TOOLS.md`. No overselling.
- Optional cloud backends are acceptable only as clearly-labeled, off-by-default
  opt-ins added as extensions.

## Adding a built-in tool
1. Add `rls/tools/<tool>.py` with a `run(args)` function (lazy heavy imports).
2. Wire a subparser in `rls/cli.py`.
3. If it needs new deps, add a feature entry in `rls/deps.py:FEATURES`.
4. Update `docs/TOOLS.md` and the README dependency map.

## Adding a user tool
See `docs/ADDING-TOOLS.md` — extensions need no core changes.

## Before a PR
Run, at minimum:
```
python -m py_compile rls/*.py rls/tools/*.py
python -m rls --help
python -m rls doctor
```
State which tools you actually ran on real hardware, and your OS/GPU.
